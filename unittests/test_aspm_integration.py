"""RC5/API integration contracts, including incomplete scan coverage and immutable evidence."""

import hashlib
import json
import secrets
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, connection, transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from dojo.aspm_ingestion.models import CommitScanSetMembership, ScanRun
from dojo.aspm_ingestion.services import finalize_commit, issue_token, request_report
from dojo.aspm_ingestion.storage import private_path
from dojo.aspm_ingestion.tasks import process_job
from unittests.test_aspm_ingestion import IngestionFixture, generic


class CommitCoverageTests(IngestionFixture, APITestCase):
    def setUp(self):
        self.setup_ingestion()
        self.reader = get_user_model().objects.create_user(username="integration-reader", password=None)
        self.product.authorized_users.add(self.reader.pk)
        self.browser = Client()
        self.browser.force_login(self.reader)

    def compare(self, base, target, *, legacy=False):
        name = "scm_commit_compare" if legacy else "aspm_commit_evidence"
        response = self.browser.get(reverse(name, args=[target.pk]), {"tab": "changes", "base": base.pk, "category": "fixed"})
        self.assertEqual(response.status_code, 200)
        return response

    def comparison_rows(self, response):
        try:
            return list(response.context["observations"])
        except KeyError:
            return list(response.context["findings"])

    def test_missing_scanner_does_not_claim_fixed_on_either_comparison_route(self):
        base = self.complete(self.accepted(key="base-finding"))
        finalize_commit(base.commit, [base.scanner], scan_ids=[base.pk])
        target = self.complete(self.accepted(key="target-other-scanner", commit_sha="b" * 40,
                                             scanner_type="Trivy Scan", report=b'{"SchemaVersion":2,"Results":[]}'))
        finalize_commit(target.commit, [base.scanner, target.scanner], scan_ids=[target.pk])
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                response = self.compare(base.commit, target.commit, legacy=legacy)
                self.assertEqual(self.comparison_rows(response), [])
                self.assertContains(response, "Coverage is incomplete")

    def test_failed_scanner_does_not_claim_fixed(self):
        base = self.complete(self.accepted(key="base"))
        finalize_commit(base.commit, [base.scanner], scan_ids=[base.pk])
        failed = self.accepted(key="failed-target", commit_sha="b" * 40, report=b"invalid JSON")
        process_job("scan", str(failed.pk))
        finalize_commit(failed.commit, [failed.scanner], scan_ids=[failed.pk])
        response = self.compare(base.commit, failed.commit)
        self.assertEqual(self.comparison_rows(response), [])
        self.assertContains(response, "Coverage is incomplete")

    def test_scope_mismatch_does_not_claim_fixed(self):
        base = self.complete(self.accepted(key="base", scan_scope="full-repository"))
        target = self.complete(self.accepted(key="target", commit_sha="b" * 40, scan_scope="subdirectory",
                                             report=json.dumps({"findings": []}).encode()))
        for scan in (base, target):
            finalize_commit(scan.commit, [scan.scanner], scan_ids=[scan.pk])
        response = self.compare(base.commit, target.commit)
        self.assertEqual(self.comparison_rows(response), [])
        self.assertContains(response, "Scan scopes differ")

    def test_finalized_complete_matching_scope_can_show_absence(self):
        base = self.complete(self.accepted(key="base", scan_scope="repository-rules-v1"))
        target = self.complete(self.accepted(key="target", commit_sha="b" * 40, scan_scope="repository-rules-v1", report=json.dumps({"findings": []}).encode()))
        for scan in (base, target):
            finalize_commit(scan.commit, [scan.scanner], scan_ids=[scan.pk])
        response = self.compare(base.commit, target.commit)
        self.assertEqual([row.source_finding_id for row in self.comparison_rows(response)], [base.test.finding_set.get().pk])
        self.assertNotContains(response, "Coverage is incomplete")

    def test_comparison_uses_current_pipeline_set_and_frozen_triage(self):
        base = self.complete(self.accepted(key="base", scan_scope="repository-rules-v1"))
        target = self.complete(self.accepted(key="target-old", commit_sha="b" * 40, scan_scope="repository-rules-v1"))
        finalize_commit(base.commit, [base.scanner], scan_ids=[base.pk])
        finalize_commit(target.commit, [target.scanner], scan_ids=[target.pk])
        before = hashlib.sha256(json.dumps(list(base.observations.values_list("snapshot", flat=True)), sort_keys=True).encode()).hexdigest()
        current = self.complete(self.accepted(key="target-new", commit_sha="b" * 40, scan_scope="repository-rules-v1", report=generic("Different pipeline finding")))
        finalize_commit(current.commit, [current.scanner], scan_ids=[current.pk])
        finding = base.test.finding_set.get()
        finding.false_p = True
        finding.save(update_fields=["false_p"])
        response = self.compare(base.commit, current.commit)
        self.assertEqual([row.source_finding_id for row in self.comparison_rows(response)], [base.test.finding_set.get().pk])
        after = hashlib.sha256(json.dumps(list(base.observations.values_list("snapshot", flat=True)), sort_keys=True).encode()).hexdigest()
        self.assertEqual(before, after)

    def test_unspecified_scope_does_not_establish_remediation(self):
        base = self.complete(self.accepted(key="base"))
        target = self.complete(self.accepted(key="target", commit_sha="b" * 40, report=json.dumps({"findings": []}).encode()))
        for scan in (base, target):
            finalize_commit(scan.commit, [scan.scanner], scan_ids=[scan.pk])
        response = self.compare(base.commit, target.commit)
        self.assertEqual(self.comparison_rows(response), [])
        self.assertContains(response, "Scan scope is not declared")

    def test_finalized_failed_run_cannot_disappear_from_its_scan_set(self):
        failed = self.accepted(report=b"invalid JSON")
        process_job("scan", str(failed.pk))
        finalize_commit(failed.commit, [failed.scanner], scan_ids=[failed.pk])
        self.assertEqual(CommitScanSetMembership.objects.filter(scan=failed).count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ScanRun.objects.filter(pk=failed.pk)._raw_delete("default")
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_scan_set_membership_cannot_be_rewritten(self):
        scan = self.complete(self.accepted(key="member"))
        other = self.accepted(key="not-a-member")
        scan_set = finalize_commit(scan.commit, [scan.scanner], scan_ids=[scan.pk])
        member = CommitScanSetMembership.objects.get(scan_set=scan_set)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CommitScanSetMembership.objects.filter(pk=member.pk).update(scan=other)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CommitScanSetMembership.objects.filter(pk=member.pk)._raw_delete("default")


class IngestionSecurityTests(IngestionFixture, APITestCase):
    def setUp(self):
        self.setup_ingestion()

    def test_repository_scope_covers_status_originals_reports_and_mutations(self):
        allowed = self.complete(self.accepted(key="allowed"))
        denied = self.complete(self.accepted(key="other-repo", repository_url="https://example.org/other"))
        scan_set = finalize_commit(denied.commit, [denied.scanner], scan_ids=[denied.pk])
        report = request_report(denied.commit, scan_set.pk)
        process_job("report", str(report.pk))
        _, raw = issue_token(user=self.service, product=self.product, repository=allowed.commit.repository,
                             scopes=["submit", "status", "read", "finalize", "reports"],
                             expires_at=timezone.now() + timedelta(hours=1), label="one repository")
        self.client.credentials(HTTP_AUTHORIZATION=f"ASPM {raw}")
        self.assertEqual(self.client.get(reverse("aspm_v1:scan-detail", args=[allowed.pk])).status_code, 200)
        for name, pk in (("scan-detail", denied.pk), ("artifact", denied.pk), ("commit-scans", denied.commit_id),
                         ("reports", denied.commit_id), ("report-download", report.pk)):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse("aspm_v1:" + name, args=[pk])).status_code, 404)
        self.assertEqual(self.upload(key="forged-repo", repository_id=denied.commit.repository_id).status_code, 403)
        self.assertEqual(self.client.post(reverse("aspm_v1:finalize", args=[denied.commit_id]), {"expected_scanners": [denied.scanner]}, format="json").status_code, 404)

    def test_human_admin_cannot_use_new_machine_mutations(self):
        scan = self.accepted()
        admin = get_user_model().objects.create_superuser(username="integration-human-admin", password=None)
        self.client.credentials()
        self.client.force_authenticate(user=admin)
        self.assertEqual(self.upload(key="human-admin").status_code, 403)
        self.assertEqual(self.client.post(reverse("aspm_v1:finalize", args=[scan.commit_id]), {"expected_scanners": [scan.scanner]}, format="json").status_code, 403)
        self.assertEqual(self.client.post(reverse("aspm_v1:reports", args=[scan.commit_id]), {}, format="json").status_code, 403)

    def test_revoked_token_cannot_download_already_completed_original(self):
        scan = self.complete(self.accepted())
        self.token.revoked_at = timezone.now()
        self.token.save(update_fields=["revoked_at"])
        response = self.client.get(reverse("aspm_v1:artifact", args=[scan.pk]))
        self.assertEqual(response.status_code, 401)

    def test_integrity_failure_is_terminal_without_importing_corrupt_bytes(self):
        scan = self.accepted()
        private_path(scan.artifact_path).write_bytes(b"tampered storage")
        process_job("scan", str(scan.pk))
        scan.refresh_from_db()
        self.assertEqual((scan.status, scan.error_code), ("FAILED", "import_failed"))
        self.assertIsNone(scan.test_id)
        self.assertFalse(scan.observations.exists())

    def test_generated_html_escapes_untrusted_report_content(self):
        payload = json.dumps({"findings": [{"title": "XSS qualification", "severity": "High", "description": '<script>alert("secret")</script>'}]}).encode()
        scan = self.complete(self.accepted(report=payload))
        scan_set = finalize_commit(scan.commit, [scan.scanner], scan_ids=[scan.pk])
        report = request_report(scan.commit, scan_set.pk)
        process_job("report", str(report.pk))
        report.refresh_from_db()
        html = private_path(report.html_path).read_text()
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)

    def test_production_legacy_import_requires_product_permission(self):
        user = get_user_model().objects.create_user(username="production-human", password=secrets.token_urlsafe(24))
        self.client.credentials()
        self.client.force_authenticate(user=user)
        payload = {"scan_type": "Generic Findings Import", "product_name": self.product.name,
                   "engagement_name": "Classic assessment", "auto_create_context": True,
                   "deduplication_execution_mode": "sync"}
        with self.settings(ASPM_API_ONLY=False), patch("sys.argv", ["uwsgi", "--ini", "uwsgi.ini"]):
            response = self.client.post(reverse("importscan-list"), {
                **payload, "file": SimpleUploadedFile("scan.json", generic()),
            }, format="multipart")
            self.assertEqual(response.status_code, 403)

            self.product.authorized_users.add(user.pk)
            response = self.client.post(reverse("importscan-list"), {
                **payload, "file": SimpleUploadedFile("scan.json", generic()),
            }, format="multipart")
            self.assertEqual(response.status_code, 201)

    def test_production_flag_false_cannot_expose_browser_upload(self):
        scan = self.complete(self.accepted())
        user = get_user_model().objects.create_user(username="production-ui-human", password=secrets.token_urlsafe(24))
        self.product.authorized_users.add(user.pk)
        browser = Client()
        browser.force_login(user)
        with self.settings(ASPM_API_ONLY=False), patch("sys.argv", ["uwsgi", "--ini", "uwsgi.ini"]):
            for name, pk in (("import_scan_results_prod", self.product.pk), ("import_scan_results", scan.test.engagement_id), ("re_import_scan_results", scan.test_id)):
                with self.subTest(name=name):
                    self.assertEqual(browser.get(reverse(name, args=[pk])).status_code, 404)
            response = browser.get(reverse("new_eng_for_prod", args=[self.product.pk]))
            self.assertNotContains(response, "Import Scan Results")
