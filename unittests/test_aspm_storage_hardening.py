from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from dojo.aspm_ingestion.models import ScanRun
from dojo.aspm_ingestion.services import request_report
from dojo.aspm_ingestion.storage import private_path
from dojo.aspm_ingestion.tasks import process_job
from unittests.test_aspm_ingestion import IngestionFixture


class EvidenceDownloadIntegrityTests(IngestionFixture, APITestCase):
    def setUp(self):
        self.setup_ingestion()

    def test_corrupt_original_is_not_downloaded(self):
        scan = ScanRun.objects.get(pk=self.upload().json()["id"])
        private_path(scan.artifact_path).write_bytes(b"corrupt evidence")
        response = self.client.get(reverse("aspm_v1:artifact", args=[scan.pk]))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"corrupt evidence", response.content)

    def test_corrupt_generated_report_is_not_downloaded(self):
        scan = self.complete(self.accepted())
        report = request_report(scan.commit, expected_scanners=[scan.scanner])
        process_job("report", str(report.pk))
        report.refresh_from_db()
        private_path(report.json_path).write_bytes(b"corrupt generated report")
        response = self.client.get(reverse("aspm_v1:report-download", args=[report.pk]), {"format": "json"})
        self.assertEqual(response.status_code, 503)

    @override_settings(ASPM_MAX_REPORT_BYTES=50)
    def test_report_quota_leaves_no_published_files(self):
        scan = self.complete(self.accepted())
        report = request_report(scan.commit, expected_scanners=[scan.scanner])
        process_job("report", str(report.pk))
        report.refresh_from_db()
        self.assertEqual(report.status, "FAILED")
        self.assertEqual(report.html_path, "")
        self.assertEqual(report.json_path, "")
        self.assertFalse(list(private_path(f"reports/{report.pk}").rglob("report.*")))

    def test_missing_original_returns_safe_503(self):
        scan = self.accepted()
        private_path(scan.artifact_path).unlink()
        response = self.client.get(reverse("aspm_v1:artifact", args=[scan.pk]))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(self.directory.name.encode(), response.content)
