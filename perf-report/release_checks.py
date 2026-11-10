# ruff: noqa: INP001 -- this standalone copy is mounted into unittests
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.utils.timezone import now
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from dojo.models import Dojo_User, Engagement, Finding, Product, Product_Type, Test, Test_Type
from dojo.vulnerability.models import FindingVulnerabilityReference, Vulnerability


class ReleaseFindingPerformanceChecks(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reader = Dojo_User.objects.create_user(username="perf_fixture_reader")
        cls.token = Token.objects.create(user=cls.reader)
        product_type = Product_Type.objects.create(name="Isolated pagination product type")
        test_type = Test_Type.objects.create(name="Isolated pagination scan")
        clock = now()

        def create_test(name):
            product = Product.objects.create(name=name, prod_type=product_type, description=name)
            engagement = Engagement.objects.create(name=name, product=product, target_start=clock, target_end=clock)
            test = Test.objects.create(engagement=engagement, test_type=test_type, target_start=clock, target_end=clock)
            return product, test

        cls.allowed, allowed_test = create_test("Pagination visible")
        cls.hidden, hidden_test = create_test("Pagination hidden")
        cls.allowed.authorized_users.add(cls.reader)
        pending = [
            Finding(title=f"Finding {index:05}", severity="High", numerical_severity="S1",
                    test=allowed_test, reporter=cls.reader, active=True)
            for index in range(5015)
        ]
        pending.insert(5004, Finding(title="Hidden finding", severity="High", numerical_severity="S1",
                                     test=hidden_test, reporter=cls.reader, active=True))
        pending.insert(4998, Finding(title="Visible inactive", severity="High", numerical_severity="S1",
                                     test=allowed_test, reporter=cls.reader, active=False))
        created = Finding.objects.bulk_create(pending, batch_size=250)
        cls.hidden_finding = created[5005]
        cls.ids = [finding.pk for finding in created if finding.active and finding.test_id == allowed_test.pk]
        cls.with_refs = cls.ids[5000]
        cls.vulnerability_ids = ["CVE-2024-3094", "GHSA-8m72-6x8g-gt2f"]
        for order in reversed(range(len(cls.vulnerability_ids))):
            vulnerability = Vulnerability.objects.create(vulnerability_id=cls.vulnerability_ids[order])
            FindingVulnerabilityReference.objects.create(finding_id=cls.with_refs, vulnerability=vulnerability, order=order)

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    def get_page(self, *, fast, **overrides):
        params = {"limit": 7, "offset": 5000, "active": "true", "severity": "High", "o": "id"}
        params.update(overrides)
        if fast:
            params["fast_offset"] = 1
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get("/api/v2/findings/", params)
        self.assertEqual(response.status_code, 200)
        return response.json(), [item["sql"] for item in queries]

    def test_fast_standard_filter_order_and_prefetched_references(self):
        standard, standard_sql = self.get_page(fast=False)
        fast, fast_sql = self.get_page(fast=True)
        self.assertEqual(fast["results"], standard["results"])
        self.assertEqual(fast["count"], len(self.ids))
        self.assertEqual(standard["count"], len(self.ids))
        self.assertEqual([f["id"] for f in fast["results"]], self.ids[5000:5007])
        expected_refs = [{"vulnerability_id": value} for value in self.vulnerability_ids]
        self.assertEqual(fast["results"][0]["vulnerability_ids"], expected_refs)
        for sql in (standard_sql, fast_sql):
            self.assertEqual(sum('FROM "dojo_findingvulnerabilityreference"' in query for query in sql), 1)
        self.assertEqual(sum(" OFFSET 5000" in q and 'FROM "dojo_finding"' in q for q in fast_sql), 1)
        self.assertTrue(any(" OFFSET 5000" in q and q.split(" FROM ", 1)[0].count(",") == 0 for q in fast_sql))

        detail = self.client.get(f"/api/v2/findings/{self.with_refs}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["vulnerability_ids"], expected_refs)

    @override_settings(V3_FEATURE_LOCATIONS=False)
    def test_legacy_endpoints_still_prefetch_ordered_references(self):
        payload, sql = self.get_page(fast=True)
        expected = [{"vulnerability_id": value} for value in self.vulnerability_ids]
        self.assertEqual(payload["results"][0]["vulnerability_ids"], expected)
        self.assertEqual(sum('FROM "dojo_findingvulnerabilityreference"' in query for query in sql), 1)
        detail = self.client.get(f"/api/v2/findings/{self.with_refs}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["vulnerability_ids"], expected)

    def test_fast_falls_back_for_custom_order_and_cannot_bypass_scope(self):
        standard, _ = self.get_page(fast=False, o="-id")
        fast, sql = self.get_page(fast=True, o="-id")
        self.assertEqual(fast["results"], standard["results"])
        self.assertEqual([f["id"] for f in fast["results"]], self.ids[::-1][5000:5007])
        self.assertTrue(any(" OFFSET 5000" in q and q.split(" FROM ", 1)[0].count(",") > 1 for q in sql))

        for fast_flag in (False, True):
            denied, _ = self.get_page(fast=fast_flag, product=self.hidden.pk)
            self.assertEqual((denied["count"], denied["results"]), (0, []))
            combined, _ = self.get_page(fast=fast_flag, product=f"{self.allowed.pk},{self.hidden.pk}")
            self.assertEqual([f["id"] for f in combined["results"]], self.ids[5000:5007])
        detail = self.client.get(f"/api/v2/findings/{self.hidden_finding.pk}/")
        self.assertEqual(detail.status_code, 404)
