"""User-visible zero-finalize contracts, executed against PostgreSQL evidence guards."""
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework.test import APITestCase

from dojo.aspm_ingestion.models import GeneratedReport
from unittests.test_aspm_ingestion import IngestionFixture, generic


class ZeroFinalizeTests(IngestionFixture, APITestCase):
    def setUp(self):
        self.setup_ingestion()
        self.reader = get_user_model().objects.create_user(username="zero-reader", password=None)
        self.product.authorized_users.add(self.reader.pk)
        self.browser = Client()
        self.browser.force_login(self.reader)

    def evidence(self, commit, tab="overview", **params):
        return self.browser.get(reverse("aspm_commit_evidence", args=[commit.pk]), {"tab": tab, **params})

    def test_export_without_finalize(self):
        scan = self.complete(self.accepted())
        response = self.client.post(reverse("aspm_v1:reports", args=[scan.commit_id]), {}, format="json")
        self.assertEqual(response.status_code, 202, response.content)
        self.assertEqual(response.json()["manifest"]["scans"][0]["id"], str(scan.pk))
        self.assertFalse(response.json()["manifest"]["complete"])

    def test_findings_select_latest_rerun_without_finalize(self):
        first = self.complete(self.accepted(key="first", report=generic("Superseded result")))
        second = self.complete(self.accepted(key="second", report=generic("Current result")))
        response = self.evidence(second.commit, "findings")
        self.assertContains(response, second.observations.get().snapshot["title"])
        self.assertNotContains(response, first.observations.get().snapshot["title"])
        self.assertTrue(first.observations.exists())
        self.assertEqual(GeneratedReport.objects.count(), 0)

    def test_sequential_scanners_publish_without_waiting_or_exporting(self):
        from pathlib import Path  # noqa: PLC0415

        fixtures = Path(__file__).parent / "scans"
        scanners = [("Semgrep JSON Report", "semgrep/one_finding.json"),
                    ("Trivy Scan", "trivy/scheme_2_many_vulns.json"),
                    ("Gitleaks Scan", "gitleaks/data_one.json")]
        count = 0
        for scanner, filename in scanners:
            scan = self.accepted(key=scanner.replace(" ", "-"), scanner_type=scanner, report=(fixtures / filename).read_bytes())
            self.assertContains(self.evidence(scan.commit, "originals"), str(scan.pk))
            self.assertContains(self.evidence(scan.commit, "originals"), "ACCEPTED")
            self.complete(scan)
            count += scan.finding_count
            overview = self.evidence(scan.commit)
            self.assertEqual(overview.context["selection"]["finding_count"], count)
            self.assertFalse(overview.context["selection"]["complete"])
            self.assertTrue(scan.observations.exists())
        self.assertFalse(GeneratedReport.objects.exists())
        self.assertFalse(scan.commit.scan_sets.exists())

    def test_pending_and_failed_rerun_keep_last_success_and_history(self):
        from dojo.aspm_ingestion.models import ScanRun  # noqa: PLC0415
        from dojo.aspm_ingestion.tasks import process_job  # noqa: PLC0415

        first = self.complete(self.accepted(key="success", attempt_number=1))
        pending = self.accepted(key="pending", attempt_number=2, report=b"invalid")
        ScanRun.objects.filter(pk=pending.pk).update(status="PROCESSING")
        overview = self.evidence(first.commit)
        self.assertEqual(overview.context["selection"]["completed_ids"], [first.pk])
        self.assertTrue(overview.context["selection"]["incomplete"])
        self.assertContains(self.evidence(first.commit, "originals"), "PROCESSING")
        process_job("scan", str(pending.pk))
        self.assertContains(self.evidence(first.commit, "originals"), "FAILED")
        self.assertEqual(self.evidence(first.commit).context["selection"]["completed_ids"], [first.pk])

    def test_multiple_pipelines_require_choice(self):
        first = self.complete(self.accepted(key="p1", pipeline_id="one"))
        second = self.complete(self.accepted(key="p2", pipeline_id="two"))
        self.assertTrue(self.evidence(first.commit).context["selection"]["ambiguous"])
        response = self.client.post(reverse("aspm_v1:reports", args=[first.commit_id]), {}, format="json")
        self.assertEqual(response.status_code, 409)
        response = self.evidence(first.commit, "findings", pipeline="pipeline:two")
        self.assertEqual([row.scan_id for row in response.context["observations"]], [second.pk])
        self.assertEqual(self.evidence(first.commit, pipeline="pipeline:forged").status_code, 400)

    def test_report_freezes_selected_completed_runs_before_late_upload(self):
        import json  # noqa: PLC0415

        from dojo.aspm_ingestion.models import CommitScanSetMembership  # noqa: PLC0415
        from dojo.aspm_ingestion.services import request_report  # noqa: PLC0415
        from dojo.aspm_ingestion.storage import private_path  # noqa: PLC0415
        from dojo.aspm_ingestion.tasks import process_job  # noqa: PLC0415

        first = self.complete(self.accepted(key="original"))
        report = request_report(first.commit)
        manifest = report.manifest.copy()
        late = self.complete(self.accepted(key="late", report=generic("Late result")))
        process_job("report", str(report.pk))
        report.refresh_from_db()
        self.assertEqual(report.manifest, manifest)
        self.assertEqual(list(CommitScanSetMembership.objects.filter(scan_set=report.scan_set).values_list("scan_id", flat=True)), [first.pk])
        payload = json.loads(private_path(report.json_path).read_text())
        self.assertEqual({row["scan_id"] for row in payload["observations"]}, {str(first.pk)})
        self.assertNotIn(str(late.pk), private_path(report.json_path).read_text())
        checksum = report.checksums.copy()
        process_job("report", str(report.pk))
        report.refresh_from_db()
        self.assertEqual(report.checksums, checksum)
        next_report = request_report(first.commit)
        self.assertEqual(next_report.version, report.version + 1)
        self.assertEqual(next_report.scan_set.scan_ids, [str(late.pk)])

    def test_report_accepts_explicit_ids_and_rejects_foreign_pending_and_duplicates(self):
        first = self.complete(self.accepted(key="one"))
        second = self.complete(self.accepted(key="two"))
        pending = self.accepted(key="pending")
        other = self.complete(self.accepted(key="other", commit_sha="b" * 40))
        url = reverse("aspm_v1:reports", args=[first.commit_id])
        for ids in ([pending.pk], [other.pk], [first.pk, second.pk]):
            response = self.client.post(url, {"scan_ids": [str(pk) for pk in ids]}, format="json")
            self.assertEqual(response.status_code, 400, response.content)
        response = self.client.post(url, {"scan_ids": [str(first.pk)]}, format="json")
        self.assertEqual(response.status_code, 202, response.content)
        self.assertEqual(response.json()["manifest"]["scans"][0]["id"], str(first.pk))

    def test_expected_scanners_are_optional_and_do_not_imply_complete_early(self):
        import json  # noqa: PLC0415

        first = self.complete(self.accepted(key="one", expected_scanners=json.dumps(["Generic Findings Import", "Trivy Scan"])))
        selection = self.evidence(first.commit).context["selection"]
        self.assertTrue(selection["coverage_known"])
        self.assertFalse(selection["complete"])
        second = self.complete(self.accepted(key="two", scanner_type="Trivy Scan", report=b'{"SchemaVersion":2,"Results":[]}'))
        self.assertTrue(self.evidence(second.commit).context["selection"]["complete"])

    def test_diff_pending_missing_and_pipeline_mismatch_never_claim_fixed(self):
        import json  # noqa: PLC0415

        declaration = json.dumps(["Generic Findings Import"])
        first = self.complete(self.accepted(key="base", scan_scope="full", expected_scanners=declaration, pipeline_id="one"))
        target = self.accepted(key="target", commit_sha="b" * 40, scan_scope="full", pipeline_id="two", expected_scanners=declaration, report=b'{"findings":[]}')
        for completed in (False, True):
            if completed:
                self.complete(target)
            response = self.evidence(target.commit, "changes", base=first.commit_id, category="fixed")
            self.assertEqual(list(response.context["observations"]), [])
            self.assertContains(response, "UNKNOWN")

    def test_diff_declared_matching_coverage_works_without_finalize(self):
        import json  # noqa: PLC0415

        declaration = json.dumps(["Generic Findings Import"])
        first = self.complete(self.accepted(key="base", scan_scope="full", expected_scanners=declaration))
        target = self.complete(self.accepted(key="target", commit_sha="b" * 40, scan_scope="full", expected_scanners=declaration, report=b'{"findings":[]}'))
        response = self.evidence(target.commit, "changes", base=first.commit_id, category="fixed")
        self.assertEqual([row.scan_id for row in response.context["observations"]], [first.pk])
        self.assertEqual(response.context["coverage_warning"], "")

    def test_polling_only_queries_metadata_and_enforces_rbac(self):
        from django.db import connection  # noqa: PLC0415
        from django.test.utils import CaptureQueriesContext  # noqa: PLC0415

        scan = self.accepted()
        url = reverse("aspm_commit_state", args=[scan.commit_id])
        with CaptureQueriesContext(connection) as captured:
            initial = self.browser.get(url)
        self.assertEqual(initial.status_code, 200)
        self.assertFalse(any("dojo_findingobservation" in row["sql"] for row in captured))
        self.complete(scan)
        self.assertNotEqual(initial.json(), self.browser.get(url).json())
        outsider = get_user_model().objects.create_user(username="outside", password=None)
        self.browser.force_login(outsider)
        for name in ("aspm_commit_state", "aspm_commit_evidence"):
            self.assertEqual(self.browser.get(reverse(name, args=[scan.commit_id])).status_code, 404)
        self.assertEqual(self.browser.post(reverse("aspm_create_report", args=[scan.commit_id])).status_code, 404)

    def test_browser_export_is_csrf_protected_and_never_accepts_scan_upload(self):
        scan = self.complete(self.accepted())
        admin = get_user_model().objects.create_superuser(username="export-admin", password=None)
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(admin)
        url = reverse("aspm_create_report", args=[scan.commit_id])
        self.assertEqual(browser.post(url).status_code, 403)
        page = browser.get(reverse("aspm_commit_evidence", args=[scan.commit_id]), {"tab": "reports"})
        self.assertContains(page, "Generate fixed HTML / JSON export")
        self.assertNotContains(page, 'type="file"')
        response = browser.post(url, {"csrfmiddlewaretoken": browser.cookies["csrftoken"].value})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(GeneratedReport.objects.count(), 1)

    def test_independent_jobs_need_explicit_choice_but_attempts_are_ordered(self):
        first = self.complete(self.accepted(key="one", pipeline_id="same", job_id="job1", attempt_number=1))
        second = self.complete(self.accepted(key="two", pipeline_id="same", job_id="job2", attempt_number=1))
        self.assertTrue(self.evidence(first.commit).context["selection"]["ambiguous"])
        response = self.evidence(first.commit, "findings", scan_ids=[str(second.pk)])
        self.assertEqual([row.scan_id for row in response.context["observations"]], [second.pk])
        self.assertEqual(self.evidence(first.commit, scan_ids=["invalid"]).status_code, 400)

    def test_standard_commit_page_shows_accepted_scan(self):
        scan = self.accepted()
        response = self.browser.get(reverse("scm_commit_detail", args=[scan.commit_id]), {"tab": "originals"})
        self.assertContains(response, str(scan.pk))
        self.assertContains(response, "ACCEPTED")

    def test_comparison_can_pin_immutable_generated_versions(self):
        from dojo.aspm_ingestion.services import request_report  # noqa: PLC0415
        from dojo.aspm_ingestion.tasks import process_job  # noqa: PLC0415

        base = self.complete(self.accepted(key="base-version", scan_scope="full"))
        target = self.complete(self.accepted(key="target-version", commit_sha="b" * 40, scan_scope="full", report=b'{"findings":[]}'))
        before = request_report(base.commit, scan_ids=[base.pk], expected_scanners=[base.scanner])
        after = request_report(target.commit, scan_ids=[target.pk], expected_scanners=[target.scanner])
        for report in (before, after):
            process_job("report", str(report.pk))
        self.complete(self.accepted(key="late-target-version", commit_sha="b" * 40, scan_scope="full"))
        response = self.evidence(target.commit, "changes", base=base.commit_id, category="fixed", base_report=str(before.pk), target_report=str(after.pk))
        self.assertEqual([row.scan_id for row in response.context["observations"]], [base.pk])
        self.assertEqual(response.context["coverage_warning"], "")
        invalid = self.evidence(target.commit, "changes", base=base.commit_id, category="fixed", target_report=str(before.pk))
        self.assertEqual(invalid.status_code, 400)

    def test_explicit_selection_pagination_preserves_all_ids(self):
        import json  # noqa: PLC0415

        first = self.complete(self.accepted(key="scope-one", scan_scope="one", report=json.dumps({"findings": [{"title": f"Scope 1 finding {i}", "severity": "High", "description": "Pagination fixture"} for i in range(35)]}).encode()))
        second = self.complete(self.accepted(key="scope-two", scan_scope="two", report=json.dumps({"findings": [{"title": f"Scope 2 finding {i}", "severity": "High", "description": "Pagination fixture"} for i in range(35)]}).encode()))
        response = self.evidence(first.commit, "findings", scan_ids=[str(first.pk), str(second.pk)])
        self.assertEqual(len(response.context["observations"]), 50)
        self.assertIn(str(first.pk), response.context["next_url"])
        self.assertIn(str(second.pk), response.context["next_url"])
        page = self.browser.get(reverse("aspm_commit_evidence", args=[first.commit_id]) + response.context["next_url"])
        self.assertEqual(len(page.context["observations"]), 20)

    def test_existing_duplicate_environment_names_do_not_fail_scan(self):
        from dojo.models import Development_Environment  # noqa: PLC0415

        Development_Environment.objects.bulk_create([Development_Environment(name="Development")])
        scan = self.complete(self.accepted())
        self.assertEqual(scan.status, "COMPLETED")
        self.assertEqual(scan.test.environment_id, Development_Environment.objects.filter(name="Development").order_by("pk").first().pk)
