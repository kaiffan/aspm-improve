from pathlib import Path

from django.urls import reverse
from rest_framework.test import APITestCase

from dojo.aspm_ingestion.tasks import process_job
from unittests.test_aspm_ingestion import IngestionFixture


class ScannerCompatibilityTests(IngestionFixture, APITestCase):
    def setUp(self):
        self.setup_ingestion()

    def test_existing_formats_through_ingestion_worker_and_generated_report(self):
        cases = (
            ("Dependency Track Finding Packaging Format (FPF) Export", "dependency_track/one_finding.json"),
            ("Semgrep JSON Report", "semgrep/one_finding.json"),
            ("Trivy Scan", "trivy/scheme_2_many_vulns.json"),
            ("KICS Scan", "kics/many_findings.json"),
            ("Fortify Scan", "fortify/fortify_few_findings.xml"),
            ("ffuf Scan", "ffuf/ffuf_one_vuln.json"),
        )
        scans = Path(__file__).parent / "scans"
        scan_ids = []
        for index, (scanner, fixture) in enumerate(cases):
            with self.subTest(scanner=scanner):
                scan = self.accepted(key=f"scanner-{index}", scanner_type=scanner, report=(scans / fixture).read_bytes(), filename=Path(fixture).name, pipeline_id="qualification", job_id=f"job-{index}")
                self.complete(scan)
                self.assertGreater(scan.finding_count, 0)
                self.assertEqual(scan.observations.count(), scan.finding_count)
                scan_ids.append(str(scan.pk))
        response = self.client.post(reverse("aspm_v1:reports", args=(scan.commit_id,)), {"scan_ids": scan_ids}, format="json")
        self.assertEqual(response.status_code, 202, response.content[:1000])
        report_id = response.json()["id"]
        process_job("report", report_id)
        download = self.client.get(reverse("aspm_v1:report-download", args=(report_id,)))
        self.assertEqual(download.status_code, 200)
        self.assertTrue(b"".join(download.streaming_content))
