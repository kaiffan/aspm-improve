from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from dojo.home.views import get_severities_all, get_severities_by_month
from dojo.models import Engagement, Finding, Risk_Acceptance, Test
from dojo.product.queries import get_active_finding_counts_by_product
from dojo.utils import get_punchcard_data
from unittests import test_round4_performance as round4
from unittests.dojo_test_case import DojoTestCase, versioned_fixtures


@versioned_fixtures
class TestRound5Performance(DojoTestCase):
    fixtures = ["dojo_testdata.json"]
    setUp = round4.TestRound4Performance.setUp

    def test_dashboard_charts_share_one_aggregate_and_preserve_boundaries(self):
        self.client.force_login(self.reader)
        for zone in ("UTC", "America/New_York"):
            with timezone.override(zone):
                today = timezone.now().date()
                cutoff = timezone.make_aware(datetime.combine(today - relativedelta(months=6), datetime.min.time()))
                self.scope.update(duplicate=False)
                self.scope.filter(pk=self.findings[0].pk).update(created=cutoff - timedelta(seconds=1))
                self.scope.filter(pk=self.findings[1].pk).update(created=cutoff, severity="Unknown")
                self.scope.filter(pk=self.findings[2].pk).update(created=timezone.now() + timedelta(days=1))
                with CaptureQueriesContext(connection) as queries:
                    response = self.client.get(reverse("dashboard"))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["by_month"], get_severities_by_month(self.scope, today))
                for severity, key in (("High", "high"), ("Low", "low"), ("Info", "info")):
                    self.assertEqual(response.context[key], get_severities_all(self.scope).get(severity, 0))
                self.assertEqual((response.context["punchcard"], response.context["ticks"]), get_punchcard_data(self.scope, today - relativedelta(weeks=26), 26))
                chart_queries = [q["sql"] for q in queries if 'FROM "dojo_finding"' in q["sql"] and "GROUP BY" in q["sql"]]
                self.assertEqual(len(chart_queries), 1)

    def test_single_product_counts_do_not_join_each_finding_to_test(self):
        with CaptureQueriesContext(connection) as queries:
            result = get_active_finding_counts_by_product([self.product.pk])
        self.assertEqual(result, {self.product.pk: (2, 1)})
        self.assertEqual(len(queries), 1)
        self.assertNotIn('"dojo_finding"."test_id" = "dojo_test"."id"', queries[0]["sql"])
        self.assertEqual(get_active_finding_counts_by_product([self.other.pk]), {})
        self.assertEqual(get_active_finding_counts_by_product([]), {})
        self.assertEqual(get_active_finding_counts_by_product([self.product.pk, self.other.pk]), result)

    def test_full_product_response_keeps_order_count_and_visibility(self):
        self.client.force_login(self.reader)
        self.scope.filter(pk=self.findings[1].pk).update(duplicate=True)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("product-list"), {"limit": 100})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual([row["id"] for row in data["results"]], [self.product.pk])
        product = data["results"][0]
        self.assertEqual(product["findings_list"], sorted(f.pk for f in self.findings[:2]))
        self.assertEqual(product["findings_count"], 2)
        aggregates = [q["sql"] for q in queries if "ARRAY_AGG" in q["sql"]]
        self.assertEqual(len(aggregates), 1)
        self.assertNotIn('"dojo_finding"."test_id" = "dojo_test"."id"', aggregates[0])
        detail = self.client.get(reverse("product-detail", args=[self.product.pk]))
        self.assertEqual(detail.status_code, 200)
        detail_data = detail.json()
        self.assertEqual(detail_data.pop("prefetch"), {})
        self.assertEqual(detail_data, product)
        self.assertIn(self.client.get(reverse("product-detail", args=[self.other.pk])).status_code, (403, 404))
        filtered = self.client.get(reverse("product-list"), {"id": self.other.pk})
        self.assertEqual(filtered.json()["results"], [])
        for mode in ("count", "none"):
            lightweight = self.client.get(reverse("product-list"), {"findings": mode}).json()["results"][0]
            self.assertNotIn("findings_list", lightweight)
            if mode == "count":
                self.assertEqual(lightweight["findings_count"], 2)
            else:
                self.assertNotIn("findings_count", lightweight)
        self.client.force_login(self.admin)
        empty = self.client.get(reverse("product-detail", args=[self.other.pk])).json()
        self.assertEqual(empty["findings_list"], [])
        self.assertEqual(empty["findings_count"], 0)

    def test_dashboard_exact_counters_exclude_duplicates_and_hidden_findings(self):
        self.scope.update(date=timezone.localdate(), mitigated=timezone.now(), duplicate=False)
        for name in ("first", "second"):
            acceptance = Risk_Acceptance.objects.create(name=name, owner=self.admin)
            acceptance.accepted_findings.add(*self.findings)
        self.scope.filter(pk=self.findings[2].pk).update(duplicate=True)
        Finding.objects.create(test=self.findings[0].test, title="extra", severity="Medium", duplicate=False)
        now = timezone.now()
        hidden_engagement = Engagement.objects.create(product=self.other, target_start=now.date(), target_end=now.date())
        hidden_test = Test.objects.create(engagement=hidden_engagement, test_type=self.findings[0].test.test_type, target_start=now, target_end=now)
        hidden = Finding.objects.create(test=hidden_test, title="hidden", severity="Critical", duplicate=False, date=now.date(), mitigated=now)
        self.client.force_login(self.reader)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("dashboard"))
        dashboard_queries = [query["sql"] for query in queries]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["finding_count"], 3)
        self.assertEqual(response.context["mitigated_count"], 2)
        self.assertEqual(response.context["accepted_count"], 2)
        self.assertEqual(response.context["high"], 1)
        self.assertEqual(response.context["low"], 1)
        self.assertEqual(response.context["info"], 0)
        self.assertEqual(response.context["critical"], 0)
        filtered = self.client.get("/api/v2/findings/", {"test__engagement__product": self.other.pk})
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.json()["count"], 0)
        self.assertEqual(filtered.json()["results"], [])
        self.assertIn(self.client.get(f"/api/v2/findings/{hidden.pk}/").status_code, (403, 404))
        counts = [sql for sql in dashboard_queries if 'FROM "dojo_finding"' in sql and "COUNT(*)" in sql]
        self.assertEqual(len(counts), 3)
        self.assertTrue(all('"description"' not in q for q in counts))
