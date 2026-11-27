import hashlib
from io import StringIO
from pathlib import Path
from unittest import skipUnless
from unittest.mock import patch
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from dojo.aspm_ingestion.models import FindingObservation, IngestionJob, ScanRun, StoredObject
from dojo.aspm_ingestion.object_store import ObjectTransportError, ObjectUnavailableError, S3ObjectStore
from dojo.aspm_ingestion.services import request_report
from dojo.aspm_ingestion.storage import PrivateMediaStorage, private_path
from dojo.aspm_ingestion.tasks import process_job
from unittests.test_aspm_ingestion import IngestionFixture, generic


@skipUnless(settings.ASPM_S3["endpoint"], "Requires a dedicated private S3 qualification bucket.")
@override_settings(ASPM_STORAGE_BACKEND="s3")
class AspmObjectStorageTests(IngestionFixture, APITestCase):
    def setUp(self):
        self.setup_ingestion()
        prefix = f'{settings.ASPM_S3["prefix"]}/tests-{uuid4().hex}'.strip("/")
        cfg = {**settings.ASPM_S3, "prefix": prefix}
        self.enterContext(override_settings(ASPM_S3=cfg))
        self.store = S3ObjectStore()
        self.objects = StoredObject.objects.filter(object_key__startswith=f"{prefix}/")

    def test_scan_acceptance_is_durable_and_duplicate_reuses_object(self):
        scan = self.accepted()
        self.assertEqual(self.upload().status_code, 200)
        self.assertEqual(self.objects.count(), 1)
        obj = self.objects.get()
        self.assertEqual(obj.state, StoredObject.State.READY)
        self.assertTrue(obj.version_id)
        self.assertTrue(obj.object_key.endswith("/artifact"))
        self.store.verify(obj)
        self.assertEqual(IngestionJob.objects.get().scan_id, scan.pk)
        self.assertEqual(self.upload(report=generic("another delivery")).status_code, 409)
        self.assertEqual(self.objects.count(), 1)

    def test_known_storage_failure_does_not_register_accepted_scan(self):
        with patch.object(S3ObjectStore, "put", side_effect=ObjectUnavailableError):
            response = self.upload()
        self.assertEqual(response.status_code, 503)
        self.assertFalse(ScanRun.objects.exists())
        self.assertFalse(IngestionJob.objects.exists())
        self.assertEqual(self.objects.get().state, StoredObject.State.STAGED)

    def test_download_is_version_pinned_and_rejects_missing_version(self):
        scan = self.accepted()
        obj = self.objects.get()
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
        self.assertEqual(self.objects.filter(state=StoredObject.State.READY).count(), 3)
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
        self.assertEqual(self.objects.filter(state=StoredObject.State.READY).count(), 3)

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
        result = self.store.client.head_object(**self.store.address(self.objects.get()))
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

    def test_filesystem_copy_resumes_and_keeps_source_and_logical_key(self):
        with self.settings(ASPM_STORAGE_BACKEND="filesystem"):
            scan = self.complete(self.accepted())
            report = request_report(scan.commit, expected_scanners=[scan.scanner])
            process_job("report", str(report.pk))
            report.refresh_from_db()
            plan = StringIO()
            call_command("aspm_storage_transfer", "plan", stdout=plan)
            self.assertIn(scan.artifact_path, plan.getvalue())
            self.assertFalse(self.objects.exists())
            call_command("aspm_storage_transfer", "copy", writers_paused=True)
            versions = dict(self.objects.values_list("name", "version_id"))
            self.assertEqual(len(versions), 3)
            call_command("aspm_storage_transfer", "copy", writers_paused=True)
            self.assertEqual(dict(self.objects.values_list("name", "version_id")), versions)
            self.assertEqual(private_path(scan.artifact_path).read_bytes(), generic())
            call_command("aspm_storage_transfer", "verify", writers_paused=True)
        response = self.client.get(reverse("aspm_v1:artifact", args=[scan.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), generic())

    def test_generated_multipart_export_can_be_verified(self):
        snapshot = {"title": "Large report fixture", "severity": "Low", "description": "A" * (1024 * 1024)}

        def write_observations(scan):
            FindingObservation.objects.bulk_create([
                FindingObservation(scan=scan, generation=scan.attempt, source_finding_id=100000 + i,
                                   identity=f"{i:064x}", severity="Low", snapshot=snapshot)
                for i in range(34)
            ], batch_size=4)
            return 34, {"Low": 34}, 0

        with patch("dojo.aspm_ingestion.tasks.snapshot_findings", side_effect=write_observations):
            scan = self.complete(self.accepted())
        report = request_report(scan.commit, expected_scanners=[scan.scanner])
        process_job("report", str(report.pk))
        report.refresh_from_db()
        self.assertEqual(report.status, ScanRun.Status.COMPLETED)
        for kind, key in (("html", report.html_path), ("json", report.json_path)):
            obj = self.objects.get(name=f"private/{key}")
            self.assertGreater(obj.size, 32 * 1024 * 1024)
            result = self.store.client.head_object(**self.store.address(obj))
            self.assertIn("-", result["ETag"])
            response = self.client.get(reverse("aspm_v1:report-download", args=[report.pk]), {"format": kind})
            self.assertEqual(response.status_code, 200)
            digest = hashlib.sha256()
            for chunk in response.streaming_content:
                digest.update(chunk)
            self.assertEqual(digest.hexdigest(), report.checksums[kind])

    def test_media_has_an_application_url_and_verifies_bytes(self):
        storage = PrivateMediaStorage()
        name = storage.save("uploaded_files/unsafe name.png", ContentFile(b"small sample image"))
        self.assertEqual(Path(name).suffix, ".png")
        self.assertNotIn("unsafe", name)
        self.assertEqual(storage.url(name), f'{settings.MEDIA_URL.rstrip("/")}/{name}')
        with storage.open(name) as source:
            self.assertEqual(source.read(), b"small sample image")
        self.assertEqual(storage.size(name), 18)
