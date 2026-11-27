import hashlib
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, close_old_connections, connections, transaction
from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from dojo.aspm_ingestion.models import FindingObservation, IngestionJob, IngestionToken, ScanRun
from dojo.aspm_ingestion.services import finalize_commit, issue_token, request_report, retry_scan
from dojo.aspm_ingestion.storage import private_path
from dojo.aspm_ingestion.tasks import dispatch_jobs, import_scan, process_job
from dojo.models import Development_Environment, Finding, Product, Product_Type, Test_Type
from dojo.scm.models import Commit, Repository

SHA = "a" * 40
URL = "https://github.com/example/application"
SCOPES = ["submit", "status", "read", "finalize", "reports"]


def generic(title="Historical finding"):
    return json.dumps({"findings": [{"title": title, "description": "Immutable evidence", "severity": "High", "cwe": 79, "vulnerability_ids": ["CVE-2026-0001"]}]}).encode()


class IngestionFixture:
    def setup_ingestion(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(ASPM_ARTIFACT_ROOT=self.directory.name, ASPM_INGESTION_ENABLED=True, ASPM_SCM_HIERARCHY=True, ASPM_API_ONLY=True)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        product_type, = Product_Type.objects.bulk_create([Product_Type(name="ASPM ingestion tests")])
        self.product, self.hidden = Product.objects.bulk_create([
            Product(name="Allowed project", description="Tests", prod_type=product_type),
            Product(name="Other project", description="Hidden", prod_type=product_type),
        ])
        self.service = get_user_model().objects.create_user(username="ingestion-ci", password=None)
        self.token, self.raw = issue_token(user=self.service, product=self.product, scopes=SCOPES, expires_at=timezone.now() + timedelta(days=1), label="unit CI")
        self.environment, self.created_environment = Development_Environment.objects.get_or_create(name="Development")
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"ASPM {self.raw}")
        self.wake = patch("dojo.aspm_ingestion.services.wake_dispatcher")
        self.wake.start()
        self.addCleanup(self.wake.stop)

    def upload(self, key="pipeline/job/attempt-1", report=None, *, filename="report.json", **changes):
        data = {"project_id": self.product.pk, "repository_url": URL, "commit_sha": SHA,
                "scanner_type": "Generic Findings Import", "idempotency_key": key,
                "file": SimpleUploadedFile(filename, generic() if report is None else report, content_type="application/json"), **changes}
        return self.client.post(reverse("aspm_v1:scans"), data, format="multipart")

    def accepted(self, **kwargs):
        response = self.upload(**kwargs)
        self.assertEqual(response.status_code, 202, response.content[:1000])
        return ScanRun.objects.get(pk=response.json()["id"])

    def complete(self, scan):
        # Direct import deliberately surfaces tracebacks if a pipeline integration fails.
        scan.attempt += 1
        scan.started_at = timezone.now()
        ScanRun.objects.filter(pk=scan.pk).update(status="PROCESSING", attempt=scan.attempt, started_at=scan.started_at)
        import_scan(scan)
        scan.refresh_from_db()
        self.assertEqual(scan.status, "COMPLETED")
        return scan


class AspmIngestionTests(IngestionFixture, APITestCase):
    def setUp(self):
        self.setup_ingestion()

    def test_semgrep_and_trivy_share_commit_and_preserve_original_bytes(self):
        scans = Path(__file__).parent / "scans"
        semgrep = (scans / "semgrep/one_finding.json").read_bytes()
        trivy = (scans / "trivy/scheme_2_many_vulns.json").read_bytes()
        first = self.accepted(key="semgrep-job-1", report=semgrep, scanner_type="Semgrep JSON Report")
        second = self.accepted(key="trivy-job-1", report=trivy, scanner_type="Trivy Scan")
        self.assertEqual(first.commit_id, second.commit_id)
        for scan, data in ((first, semgrep), (second, trivy)):
            self.assertEqual(private_path(scan.artifact_path).read_bytes(), data)
            self.assertEqual(scan.artifact_sha256, hashlib.sha256(data).hexdigest())
            self.complete(scan)
            self.assertGreater(scan.finding_count, 0)
            if scan.scanner == "Trivy Scan":
                ids = [value for row in scan.observations.values_list("snapshot", flat=True) for value in row["vulnerability_ids"]]
                self.assertIn("CVE-2020-15999", ids)

    def test_repeat_delivery_and_conflict(self):
        first = self.accepted()
        response = self.upload()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], str(first.pk))
        self.assertEqual(ScanRun.objects.count(), 1)
        self.assertEqual(IngestionJob.objects.count(), 1)
        self.assertEqual(len(list(Path(self.directory.name).glob("originals/*/artifact"))), 1)
        self.assertEqual(self.upload(report=generic("Changed")).status_code, 409)
        self.assertEqual(self.upload(branch="changed").status_code, 409)
        self.assertEqual(self.upload(commit_sha="b" * 40).status_code, 409)

    def test_misconfigured_private_storage_rejects_acceptance_with_service_unavailable(self):
        with self.settings(
            ASPM_STORAGE_BACKEND="filesystem",
            MEDIA_ROOT=self.directory.name,
            ASPM_ARTIFACT_ROOT=self.directory.name,
        ):
            response = self.upload()
        self.assertEqual(response.status_code, 503)
        self.assertFalse(ScanRun.objects.exists())
        self.assertFalse(IngestionJob.objects.exists())

    def test_independent_attempts_keep_history(self):
        first = self.complete(self.accepted(key="job/1", attempt_number=1))
        second = self.complete(self.accepted(key="job/2", attempt_number=2))
        self.assertNotEqual(first.test_id, second.test_id)
        self.assertEqual(first.commit_id, second.commit_id)
        self.assertTrue(FindingObservation.objects.filter(scan=first).exists())

    def test_next_commit_and_live_finding_edits_do_not_change_old_observations(self):
        first = self.complete(self.accepted())
        before = list(first.observations.values_list("snapshot", flat=True))
        second = self.complete(self.accepted(key="next-commit", commit_sha="b" * 40, report=generic("New title")))
        self.assertNotEqual(first.test_id, second.test_id)
        finding = Finding.objects.get(test=first.test)
        finding.title = "Edited after import"
        finding.save()
        self.assertEqual(list(first.observations.values_list("snapshot", flat=True)), before)

    def test_generated_report_has_frozen_manifest_and_bytes(self):
        scan = self.complete(self.accepted())
        scan_set = finalize_commit(scan.commit, [scan.scanner, "Trivy Scan"])
        report = request_report(scan.commit, scan_set.pk)
        process_job("report", str(report.pk))
        report.refresh_from_db()
        self.assertEqual(report.status, "COMPLETED")
        before = private_path(report.json_path).read_bytes()
        payload = json.loads(before)
        self.assertEqual([item["id"] for item in payload["report"]["scans"]], [str(scan.pk)])
        self.assertEqual(len(payload["observations"]), scan.finding_count)
        self.assertIn("CVE-2026-0001", payload["observations"][0]["vulnerability_ids"])
        self.assertFalse(payload["report"]["complete"])
        self.assertEqual(payload["report"]["missing_scanners"], ["Trivy Scan"])
        self.complete(self.accepted(key="late-trivy", report=b'{"SchemaVersion":2,"Results":[]}', scanner_type="Trivy Scan"))
        self.assertEqual(private_path(report.json_path).read_bytes(), before)
        self.assertEqual(report.manifest["scans"][0]["id"], str(scan.pk))
        second_set = finalize_commit(scan.commit, [scan.scanner, "Trivy Scan"])
        second = request_report(scan.commit, second_set.pk)
        self.assertEqual(second.version, 2)
        self.assertTrue(second.manifest["complete"])
        for kind in ("json", "html"):
            response = self.client.get(reverse("aspm_v1:report-download", args=[report.pk]), {"format": kind})
            self.assertEqual(response.status_code, 200, getattr(response, "data", None))
            self.assertTrue(b"ASPM" in b"".join(response.streaming_content) if kind == "html" else True)

    def test_report_does_not_require_explicit_finalization(self):
        scan = self.complete(self.accepted())
        response = self.client.post(reverse("aspm_v1:reports", args=[scan.commit_id]), {}, format="json")
        self.assertEqual(response.status_code, 202)

    def test_finalize_pins_pipeline_attempt_and_rejects_another_commit(self):
        failed = self.accepted(key="older-job", report=b"invalid JSON")
        process_job("scan", str(failed.pk))
        current = self.complete(self.accepted(key="new-job-attempt", attempt_number=2))
        other = self.complete(self.accepted(key="another-commit", commit_sha="b" * 40))
        url = reverse("aspm_v1:finalize", args=[current.commit_id])
        invalid = self.client.post(url, {"expected_scanners": [current.scanner], "scan_ids": [str(other.pk)]}, format="json")
        self.assertEqual(invalid.status_code, 400)
        response = self.client.post(url, {"expected_scanners": [current.scanner], "scan_ids": [str(current.pk)]}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["scan_ids"], [str(current.pk)])
        report = request_report(current.commit, response.json()["id"])
        self.assertTrue(report.manifest["complete"])
        failed.refresh_from_db()
        self.assertEqual(failed.status, "FAILED")

    def test_scope_product_repository_user_and_token_lifecycle(self):
        self.assertEqual(self.upload(project_id=self.hidden.pk).status_code, 403)
        hidden_repo = Repository.objects.create(product=self.hidden, url=URL)
        self.assertEqual(self.upload(repository_id=hidden_repo.pk).status_code, 403)
        repository = Repository.objects.create(product=self.product, url=URL)
        scoped, raw = issue_token(user=self.service, product=self.product, repository=repository, scopes=SCOPES, expires_at=timezone.now() + timedelta(hours=1), label="repo")
        self.client.credentials(HTTP_AUTHORIZATION=f"ASPM {raw}")
        self.assertEqual(self.upload(repository_url="https://github.com/example/other").status_code, 403)
        scan = self.accepted()
        other_user = get_user_model().objects.create_user(username="other-ci", password=None)
        _, other_raw = issue_token(user=other_user, product=self.product, scopes=SCOPES, expires_at=timezone.now() + timedelta(hours=1), label="other")
        self.client.credentials(HTTP_AUTHORIZATION=f"ASPM {other_raw}")
        self.assertEqual(self.client.get(reverse("aspm_v1:scan-detail", args=[scan.pk])).status_code, 404)
        self.client.credentials(HTTP_AUTHORIZATION=f"ASPM {raw}")
        IngestionToken.objects.filter(pk=scoped.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.upload().status_code, 401)
        IngestionToken.objects.filter(pk=scoped.pk).update(expires_at=timezone.now() + timedelta(hours=1), revoked_at=timezone.now())
        self.assertEqual(self.upload().status_code, 401)
        self.assertEqual(ScanRun.objects.count(), 1)

    def test_native_principal_uses_classic_import_without_aspm_submit_scope(self):
        scan = self.accepted()
        user = get_user_model().objects.create_user(username="human", password=None)
        user.set_password("test-human-password")
        user.save()
        self.product.authorized_users.add(user.pk)
        self.client.credentials()
        self.client.force_authenticate(user=user)
        self.assertEqual(self.upload(key="human").status_code, 403)
        legacy_payload = {"scan_type": "Generic Findings Import", "product_name": self.product.name,
                          "engagement_name": "Legacy native integration", "auto_create_context": True,
                          "file": SimpleUploadedFile("scan.json", generic()), "deduplication_execution_mode": "sync"}
        response = self.client.post(reverse("importscan-list"), legacy_payload, format="multipart")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(ScanRun.objects.count(), 1)
        self.assertEqual(self.client.get(reverse("aspm_v1:scan-detail", args=[scan.pk])).status_code, 200)
        self.product.authorized_users.remove(user.pk)
        self.assertEqual(self.client.get(reverse("aspm_v1:scan-detail", args=[scan.pk])).status_code, 404)

    def test_legacy_machine_import_reimport_without_git_metadata(self):
        self.product.authorized_users.add(self.service.pk)
        self.client.credentials()
        self.client.force_authenticate(user=self.service)
        common = {"scan_type": "Generic Findings Import", "deduplication_execution_mode": "sync",
                  "product_name": self.product.name, "engagement_name": "Legacy integration", "auto_create_context": True}
        first = self.client.post(reverse("importscan-list"), {**common, "file": SimpleUploadedFile("scan.json", generic())}, format="multipart")
        self.assertEqual(first.status_code, 201, first.content)
        second = self.client.post(reverse("reimportscan-list"), {**common, "test": first.json()["test_id"], "file": SimpleUploadedFile("scan.json", generic())}, format="multipart")
        self.assertEqual(second.status_code, 201, second.content)
        self.assertEqual(first.json()["test_id"], second.json()["test_id"])
        self.assertEqual(ScanRun.objects.count(), 0)

    @override_settings(ASPM_MAX_SCAN_BYTES=64)
    def test_limits_parser_validation_sha_and_unsafe_names(self):
        self.assertEqual(self.upload(report=b"x" * 65).status_code, 400)
        self.assertEqual(self.upload(report=b"{}", scanner_type="Uninstalled evil parser").status_code, 400)
        self.assertEqual(self.upload(report=b"{}", commit_sha="a" * 7).status_code, 400)
        self.assertEqual(self.upload(report=b"{}", repository_url="https://secret@example.com/org/repo").status_code, 400)
        self.assertEqual(self.upload(report=b"{}", sha256="0" * 64).status_code, 400)
        self.assertFalse(ScanRun.objects.exists())

    @override_settings(ASPM_TOKEN_RATE_PER_MINUTE=1)
    def test_shared_database_rate_limit(self):
        self.assertEqual(self.upload(report=b"{}").status_code, 202)
        self.assertEqual(self.upload(key="rate-2", report=b"{}").status_code, 429)

    def test_failed_parser_and_safe_retry(self):
        scan = self.accepted(report=b"malformed JSON secret should not be exposed")
        process_job("scan", str(scan.pk))
        scan.refresh_from_db()
        self.assertEqual(scan.status, "FAILED")
        self.assertEqual(scan.error_code, "import_failed")
        self.assertEqual(scan.observations.count(), 0)
        retry_scan(scan)
        process_job("scan", str(scan.pk))
        scan.refresh_from_db()
        self.assertEqual(scan.status, "FAILED")
        self.assertEqual(scan.attempt, 2)
        self.assertEqual(ScanRun.objects.count(), 1)

    def test_duplicate_worker_message_does_not_reimport(self):
        scan = self.accepted()
        process_job("scan", str(scan.pk))
        scan.refresh_from_db()
        self.assertEqual(scan.status, "COMPLETED")
        count = Finding.objects.filter(test_id=scan.test_id).count()
        process_job("scan", str(scan.pk))
        scan.refresh_from_db()
        self.assertEqual(scan.attempt, 1)
        self.assertEqual(Finding.objects.filter(test_id=scan.test_id).count(), count)

    def test_worker_recovery_reimports_same_test_after_snapshot_crash(self):
        scan = self.accepted()
        with patch("dojo.aspm_ingestion.tasks.snapshot_findings", side_effect=RuntimeError("worker failure")):
            process_job("scan", str(scan.pk))
        scan.refresh_from_db()
        self.assertEqual(scan.status, "FAILED")
        original_test = scan.test_id
        retry_scan(scan)
        process_job("scan", str(scan.pk))
        scan.refresh_from_db()
        self.assertEqual(scan.status, "COMPLETED")
        self.assertEqual(scan.test_id, original_test)
        self.assertEqual(scan.finding_count, 1)

    def test_outbox_survives_broker_failure(self):
        scan = self.accepted()
        with patch("dojo.aspm_ingestion.tasks.process_job.apply_async", side_effect=ConnectionError):
            dispatch_jobs()
        self.assertTrue(IngestionJob.objects.filter(scan=scan).exists())
        IngestionJob.objects.filter(scan=scan).update(next_dispatch_at=timezone.now())
        with patch("dojo.aspm_ingestion.tasks.process_job.apply_async") as send:
            dispatch_jobs()
        self.assertEqual(send.call_count, 1)

    def test_database_rejects_history_rewrite_and_cross_product_links(self):
        scan = self.complete(self.accepted())
        with self.assertRaises(IntegrityError), transaction.atomic():
            ScanRun.objects.filter(pk=scan.pk).update(artifact_sha256="0" * 64)
        with self.assertRaises(IntegrityError), transaction.atomic():
            scan.observations.update(snapshot={"title": "rewritten"})
        with self.assertRaises(IntegrityError), transaction.atomic():
            Commit.objects.filter(pk=scan.commit_id).update(sha="b" * 40)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Repository.objects.filter(pk=scan.commit.repository_id).update(product=self.hidden)

    def test_ui_has_no_scan_upload_routes_or_controls(self):
        scan = self.complete(self.accepted())
        user = get_user_model().objects.create_superuser(username="ui-review", password=None)
        client = Client()
        client.force_login(user)
        for name, pk in (("import_scan_results_prod", self.product.pk), ("import_scan_results", scan.test.engagement_id), ("re_import_scan_results", scan.test_id)):
            url = reverse(name, args=[pk])
            self.assertEqual(client.get(url).status_code, 404)
            self.assertEqual(client.post(url).status_code, 404)
        for name in ("new_eng_for_prod", "new_eng_for_prod_cicd"):
            response = client.get(reverse(name, args=[self.product.pk]))
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, "Import Scan Results")
        for tab in ("overview", "originals", "reports", "findings", "changes"):
            response = client.get(reverse("aspm_commit_evidence", args=[scan.commit_id]), {"tab": tab})
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, "multipart/form-data")
            self.assertNotContains(response, "import_scan_results")
            self.assertNotContains(response, "Upload Scan")

    def test_historical_ui_uses_bounded_cursor(self):
        report = json.dumps({"findings": [{"title": f"Historical row {i}", "description": "Cursor fixture", "severity": "High"} for i in range(60)]}).encode()
        scan = self.complete(self.accepted(report=report))
        user = get_user_model().objects.create_user(username="history-reader", password=None)
        self.product.authorized_users.add(user.pk)
        client = Client()
        client.force_login(user)
        url = reverse("aspm_commit_evidence", args=[scan.commit_id])
        first = client.get(url, {"tab": "findings"})
        self.assertEqual(len(first.context["observations"]), 50)
        second = client.get(url + first.context["next_url"])
        self.assertEqual(len(second.context["observations"]), 10)
        self.assertIsNone(second.context["next_url"])
        self.assertEqual(client.get(url, {"tab": "findings", "after": "invalid"}).status_code, 400)
        self.assertEqual(client.get(url, {"tab": "changes", "base": "invalid"}).status_code, 400)


class AspmConcurrentDeliveryTests(IngestionFixture, SimpleTestCase):
    databases = {"default"}

    def setUp(self):
        self.existing_test_type_ids = set(Test_Type.objects.filter(name="Generic Findings Import").values_list("pk", flat=True))
        self.setup_ingestion()

    def tearDown(self):
        # Retained Community compatibility FKs cannot be flushed by TransactionTestCase.
        ScanRun.objects.filter(product=self.product).delete()
        Repository.objects.filter(product=self.product).delete()
        IngestionToken.objects.filter(user=self.service).delete()
        self.service.delete()
        Product.objects.filter(pk__in=[self.product.pk, self.hidden.pk]).delete()
        Product_Type.objects.filter(pk=self.product.prod_type_id).delete()
        if self.created_environment:
            self.environment.delete()
        Test_Type.objects.filter(name="Generic Findings Import").exclude(pk__in=self.existing_test_type_ids).delete()
        super().tearDown()

    def test_parallel_identical_posts_create_one_logical_scan(self):
        barrier = Barrier(4)

        def post():
            close_old_connections()
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f"ASPM {self.raw}")
            try:
                barrier.wait(timeout=10)
                response = client.post(reverse("aspm_v1:scans"), {
                    "project_id": self.product.pk, "repository_url": URL, "commit_sha": SHA,
                    "scanner_type": "Generic Findings Import", "idempotency_key": "parallel",
                    "file": SimpleUploadedFile("scan.json", generic()),
                }, format="multipart")
                return response.status_code, response.json()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: post(), range(4)))
        self.assertEqual(sorted(code for code, _ in results), [200, 200, 200, 202], results)
        self.assertEqual(len({payload["id"] for _, payload in results}), 1)
        self.assertEqual(ScanRun.objects.count(), 1)
        self.assertEqual(Commit.objects.count(), 1)
        self.assertEqual(IngestionJob.objects.count(), 1)
