import hashlib
from pathlib import Path
from unittest import skipUnless
from unittest.mock import patch

from django.conf import settings
from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from dojo.aspm_ingestion.models import IngestionJob, ScanRun, StoredObject
from dojo.aspm_ingestion.object_store import ObjectTransportError, ObjectUnavailableError, S3ObjectStore
from dojo.aspm_ingestion.services import request_report
from dojo.aspm_ingestion.storage import PrivateMediaStorage
from dojo.aspm_ingestion.tasks import process_job
from unittests.test_aspm_ingestion import IngestionFixture, generic


@skipUnless(settings.ASPM_S3["endpoint"], "Requires a dedicated private S3 qualification bucket.")
@override_settings(ASPM_STORAGE_BACKEND="s3")
class AspmObjectStorageTests(IngestionFixture, APITestCase):
    def setUp(self):
        self.setup_ingestion()
        cfg = {**settings.ASPM_S3, "prefix": f'{settings.ASPM_S3["prefix"]}/tests'}
        self.enterContext(override_settings(ASPM_S3=cfg))
        self.store = S3ObjectStore()

    def test_scan_acceptance_is_durable_and_duplicate_reuses_object(self):
        scan = self.accepted()
        self.assertEqual(self.upload().status_code, 200)
        self.assertEqual(StoredObject.objects.count(), 1)
        obj = StoredObject.objects.get()
        self.assertEqual(obj.state, StoredObject.State.READY)
        self.assertTrue(obj.version_id)
        self.assertTrue(obj.object_key.endswith("/artifact"))
        self.store.verify(obj)
        self.assertEqual(IngestionJob.objects.get().scan_id, scan.pk)
        self.assertEqual(self.upload(report=generic("another delivery")).status_code, 409)
        self.assertEqual(StoredObject.objects.count(), 1)

    def test_known_storage_failure_does_not_register_accepted_scan(self):
        with patch.object(S3ObjectStore, "put", side_effect=ObjectUnavailableError):
            response = self.upload()
        self.assertEqual(response.status_code, 503)
        self.assertFalse(ScanRun.objects.exists())
        self.assertFalse(IngestionJob.objects.exists())
        self.assertEqual(StoredObject.objects.get().state, StoredObject.State.STAGED)

    def test_download_is_version_pinned_and_rejects_missing_version(self):
        scan = self.accepted()
        obj = StoredObject.objects.get()
        response = self.client.get(reverse("aspm_v1:artifact", args=[scan.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), generic())
        self.store.client.put_object(Bucket=obj.bucket, Key=obj.object_key, Body=b"incorrect latest version")
        response = self.client.get(reverse("aspm_v1:artifact", args=[scan.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), generic())
        self.store.client.delete_object(**self.store.address(obj))
        response = self.client.get(reverse("aspm_v1:artifact", args=[scan.pk]))
        self.assertEqual(response.status_code, 503)

    def test_report_is_published_only_if_both_objects_verify(self):
        scan = self.complete(self.accepted())
        first = request_report(scan.commit, expected_scanners=[scan.scanner])
        process_job("report", str(first.pk))
        first.refresh_from_db()
        self.assertEqual(first.status, ScanRun.Status.COMPLETED)
        self.assertEqual(StoredObject.objects.filter(state=StoredObject.State.READY).count(), 3)
        response = self.client.get(reverse("aspm_v1:report-download", args=[first.pk]), {"format": "json"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(hashlib.sha256(b"".join(response.streaming_content)).hexdigest(), first.checksums["json"])
        second = request_report(scan.commit, expected_scanners=[scan.scanner])
        original = S3ObjectStore.put

        def fail_html(store, obj, source):
            if obj.content_type.startswith("text/html"):
                raise ObjectUnavailableError
            return original(store, obj, source)

        with patch.object(S3ObjectStore, "put", fail_html):
            process_job("report", str(second.pk))
        second.refresh_from_db()
        self.assertEqual(second.status, ScanRun.Status.FAILED)
        self.assertEqual((second.json_path, second.html_path), ("", ""))
        self.assertEqual(StoredObject.objects.filter(state=StoredObject.State.READY).count(), 3)

    def test_temporary_s3_failure_keeps_the_outbox_and_resumes(self):
        scan = self.accepted()
        with patch.object(S3ObjectStore, "open_verified", side_effect=ObjectTransportError):
            process_job("scan", str(scan.pk))
        scan.refresh_from_db()
        job = IngestionJob.objects.get(scan=scan)
        self.assertEqual(scan.status, ScanRun.Status.ACCEPTED)
        self.assertIsNone(scan.test_id)
        self.assertEqual(job.storage_failures, 1)
        self.assertGreater(job.storage_retry_at, timezone.now())
        process_job("scan", str(scan.pk))
        scan.refresh_from_db()
        self.assertEqual(scan.attempt, 1)
        IngestionJob.objects.filter(pk=job.pk).update(storage_retry_at=timezone.now())
        process_job("scan", str(scan.pk))
        scan.refresh_from_db()
        self.assertEqual(scan.status, ScanRun.Status.COMPLETED)
        self.assertFalse(IngestionJob.objects.filter(pk=job.pk).exists())

    def test_48_mib_file_and_multipart_abort(self):
        size = 48 * 1024 * 1024
        data = generic().ljust(size, b" ")
        scan = self.accepted(report=data, sha256=hashlib.sha256(data).hexdigest())
        self.assertEqual(scan.artifact_size, size)
        result = self.store.client.head_object(**self.store.address(StoredObject.objects.get()))
        self.assertIn("-", result["ETag"])
        put_part = self.store.client.upload_part

        def fail_second_part(**kwargs):
            if kwargs["PartNumber"] == 2:
                raise ObjectUnavailableError
            return put_part(**kwargs)

        with patch.object(self.store.client, "upload_part", side_effect=fail_second_part):
            response = self.upload(key="interrupted", report=data)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(ScanRun.objects.count(), 1)
        self.assertEqual(self.store.client.list_multipart_uploads(Bucket=self.store.bucket, Prefix=self.store.prefix).get("Uploads", []), [])

    def test_media_has_an_application_url_and_verifies_bytes(self):
        storage = PrivateMediaStorage()
        name = storage.save("uploaded_files/unsafe name.png", ContentFile(b"small sample image"))
        self.assertEqual(Path(name).suffix, ".png")
        self.assertNotIn("unsafe", name)
        self.assertEqual(storage.url(name), f'{settings.MEDIA_URL.rstrip("/")}/{name}')
        with storage.open(name) as source:
            self.assertEqual(source.read(), b"small sample image")
        self.assertEqual(storage.size(name), 18)
