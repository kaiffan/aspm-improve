import base64
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from dojo.finding.queries import get_authorized_findings_for_queryset
from dojo.models import BurpRawRequestResponse, Dojo_User, Finding, Notes
from dojo.utils import Product_Tab
from dojo.vulnerability.models import FindingVulnerabilityReference, Vulnerability
from unittests import test_round4_performance as round4
from unittests.dojo_test_case import DojoTestCase, versioned_fixtures


@versioned_fixtures
class TestFindingBrowserRecovery(DojoTestCase):
    fixtures = ["dojo_testdata.json"]
    setUp = round4.TestRound4Performance.setUp

    def product_scope(self, user=None, permission="view"):
        scope = Finding.objects.filter(test__engagement__product=self.product).order_by("-pk")
        return get_authorized_findings_for_queryset(
            permission, scope, user if user is not None else self.reader, prefer_product_join=True,
        )

    def test_product_scope_preserves_exact_rows_count_and_order(self):
        expected = sorted((finding.pk for finding in self.findings), reverse=True)
        with CaptureQueriesContext(connection) as queries:
            actual = list(self.product_scope().values_list("pk", flat=True))
        self.assertEqual(actual, expected)
        self.assertEqual(len(queries), 1)
        self.assertEqual(self.product_scope().count(), len(expected))
        self.assertNotIn("= ANY(", queries[0]["sql"])

    def test_reauthorization_of_filter_clones_keeps_product_plan(self):
        scoped = self.product_scope().filter(active=True)
        with CaptureQueriesContext(connection) as queries:
            actual = list(get_authorized_findings_for_queryset("view", scoped, self.reader))
        self.assertEqual([finding.pk for finding in actual], [self.findings[1].pk, self.findings[0].pk])
        self.assertNotIn("= ANY(", queries[0]["sql"])

    def test_default_global_scope_keeps_rc3_array_plan(self):
        with CaptureQueriesContext(connection) as queries:
            actual = list(get_authorized_findings_for_queryset("view", self.scope, self.reader))
        self.assertEqual(len(actual), len(self.findings))
        self.assertIn("= ANY(", queries[0]["sql"])

    def test_membership_and_privileged_action_denials_are_unchanged(self):
        outsider = Dojo_User.objects.create(username="browser_recovery_outsider")
        for user, permission in ((outsider, "view"), (AnonymousUser(), "view"), (self.reader, "delete")):
            with self.subTest(user=user, permission=permission):
                self.assertFalse(self.product_scope(user, permission).exists())
        self.product.authorized_users.remove(self.reader)
        self.assertFalse(self.product_scope().exists())

    def test_overlapping_product_type_membership_does_not_duplicate_rows(self):
        self.product.prod_type.authorized_users.add(self.reader)
        expected = sorted((finding.pk for finding in self.findings), reverse=True)
        self.assertEqual(list(self.product_scope().values_list("pk", flat=True)), expected)
        self.assertEqual(self.product_scope().count(), len(expected))

    def test_staff_and_superuser_preserve_the_supplied_filter(self):
        self.reader.is_staff = True
        for user in (self.reader, self.admin):
            with self.subTest(user=user):
                self.assertEqual(self.product_scope(user, "delete").count(), len(self.findings))

    def test_plugin_authorization_still_receives_and_can_deny_scoped_queryset(self):
        seen = []

        def deny(permission, queryset, user=None):
            seen.append((permission, user, queryset))
            return queryset.none()

        with patch("dojo.finding.queries.get_auth_filter", return_value=deny):
            self.assertFalse(self.product_scope().exists())
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0][:2], ("view", self.reader))

    def test_finding_page_has_complete_data_relations_and_readiness_elements(self):
        finding = self.findings[0]
        self.scope.filter(pk=finding.pk).update(
            description="Recovery complete description", mitigation="Recovery mitigation",
            impact="Recovery impact", references="https://recovery.invalid/reference",
        )
        note = Notes.objects.create(entry="Recovery evidence note", author=self.admin, date=timezone.now())
        finding.notes.add(note)
        vulnerability = Vulnerability.objects.create(vulnerability_id="CVE-2026-99001", vulnerability_id_type="CVE")
        FindingVulnerabilityReference.objects.create(finding=finding, vulnerability=vulnerability, order=0)
        BurpRawRequestResponse.objects.create(
            finding=finding,
            burpRequestBase64=base64.b64encode(b"GET /recovery HTTP/1.1\r\nHost: recovery.invalid\r\n\r\n"),
            burpResponseBase64=base64.b64encode(b"HTTP/1.1 200 OK\r\n\r\nRecovery evidence"),
        )
        self.client.force_login(self.reader)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("view_finding", args=(finding.pk,)))
        self.assertEqual(response.status_code, 200)
        for value in (finding.title, "Recovery complete description", "Recovery mitigation", "Recovery impact",
                      "recovery.invalid/reference", "Recovery evidence note", "CVE-2026-99001", 'id="vuln_desc"', "finding-title"):
            self.assertContains(response, value)
        self.assertEqual(response.context["finding"].severity, "High")
        self.assertIn(b"GET /recovery", response.context["burp_request"])
        self.assertIn(b"Recovery evidence", response.context["burp_response"])
        similar_sql = [query["sql"] for query in queries if 'FROM "dojo_finding"' in query["sql"]
                       and f'NOT ("dojo_finding"."id" = {finding.pk})' in query["sql"]]
        self.assertTrue(similar_sql)
        self.assertTrue(all("= ANY(" not in sql for sql in similar_sql))

    def test_foreign_finding_page_is_denied(self):
        self.client.force_login(self.reader)
        finding = Finding.objects.exclude(test__engagement__product=self.product).first()
        self.assertIsNotNone(finding)
        response = self.client.get(reverse("view_finding", args=(finding.pk,)))
        # The existing HTML denial handler renders 403.html with HTTP 400.
        # Preserve that contract here; API permission status tests remain separate.
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")
        self.assertNotIn(finding.title, response.content.decode())

    def test_product_tab_count_keeps_all_open_flags_and_single_request_cache(self):
        with CaptureQueriesContext(connection) as queries:
            tab = Product_Tab(self.product)
            self.assertEqual(tab.open_findings_count, 2)
            self.assertEqual(tab.open_findings_count, 2)
        self.assertEqual(len(queries), 1)
        self.assertIn("= ANY(", queries[0]["sql"])
        self.assertNotIn('"dojo_finding"."test_id" = "dojo_test"."id"', queries[0]["sql"])
        finding = self.findings[0]
        for field, value in (("false_p", True), ("duplicate", True), ("out_of_scope", True),
                             ("active", False), ("mitigated", timezone.now())):
            with self.subTest(field=field):
                self.scope.filter(pk=finding.pk).update(**{field: value})
                self.assertEqual(Product_Tab(self.product).open_findings_count, 1)
                self.scope.filter(pk=finding.pk).update(**{field: True if field == "active" else None if field == "mitigated" else False})
        self.assertEqual(Product_Tab(self.product).open_findings_count, 2)
        self.assertEqual(Product_Tab(self.other).open_findings_count, 0)

    def test_product_tab_count_includes_findings_of_archived_tests(self):
        test = self.findings[0].test
        type(test).unfiltered.filter(pk=test.pk).update(archived_at=timezone.now())
        self.assertEqual(Product_Tab(self.product).open_findings_count, 2)
