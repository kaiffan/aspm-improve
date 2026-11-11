from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.db import connection
from django.db.models import Count
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from dojo.home.views import get_severities_by_month
from dojo.models import Dojo_User, Engagement, Finding, Product, Product_Type, Test, Test_Type
from dojo.utils import get_punchcard_data
from unittests.dojo_test_case import DojoTestCase, versioned_fixtures


@versioned_fixtures
class TestRound4Performance(DojoTestCase):
    fixtures = ["dojo_testdata.json"]

    def setUp(self):
        self.admin = Dojo_User.objects.get(username="admin")
        self.reader = Dojo_User.objects.create(username="round4_reader")
        self.product = Product.objects.create(name="Round4 visible", description="Round4 test fixture", prod_type=Product_Type.objects.create(name="Round4 type", description="Round4 test fixture"))
        self.other = Product.objects.create(name="Round4 hidden", description="Round4 test fixture", prod_type=self.product.prod_type)
        self.product.authorized_users.add(self.reader)
        now = timezone.now()
        engagement = Engagement.objects.create(product=self.product, name="Round4", target_start=now.date(), target_end=now.date())
        test = Test.objects.create(engagement=engagement, test_type=Test_Type.objects.first(), target_start=now, target_end=now)
        self.findings = Finding.objects.bulk_create([
            Finding(test=test, title="r4 active verified", active=True, verified=True, severity="High"),
            Finding(test=test, title="r4 active", active=True, verified=False, severity="Low"),
            Finding(test=test, title="r4 inactive", active=False, verified=True, severity="Info"),
        ])
        self.scope = Finding.objects.filter(pk__in=[finding.pk for finding in self.findings])

    def test_product_page_batches_exact_scoped_counts(self):
        self.client.force_login(self.reader)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("product"))
        self.assertEqual(response.status_code, 200)
        rows = list(response.context["prod_list"])
        self.assertEqual([row.pk for row in rows], [self.product.pk])
        self.assertEqual((rows[0].findings_count, rows[0].active_finding_count, rows[0].active_verified_finding_count), (2, 2, 1))
        grouped = [q["sql"] for q in queries if 'FROM "dojo_finding"' in q["sql"] and "FILTER (WHERE" in q["sql"]]
        self.assertEqual(len(grouped), 1)
        for order in ("findings_count", "-findings_count", "name", "-name"):
            ordered = self.client.get(reverse("product"), {"o": order, "page_size": 1})
            self.assertEqual(ordered.status_code, 200)
            self.assertEqual([row.pk for row in ordered.context["prod_list"]], [self.product.pk])
            self.assertEqual(ordered.context["prod_list"][0].findings_count, 2)

    def test_product_page_preserves_count_order_and_page_boundaries(self):
        self.client.force_login(self.admin)
        for order, expected in (("-findings_count", [self.product.pk, self.other.pk]), ("findings_count", [self.other.pk, self.product.pk])):
            actual = []
            for page in (1, 2):
                response = self.client.get(reverse("product"), {"name": "Round4", "o": order, "page_size": 1, "page": page})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["prod_list"].paginator.count, 2)
                actual.extend(product.pk for product in response.context["prod_list"])
            self.assertEqual(actual, expected)

    def test_dashboard_months_preserve_cutoff_unknown_severity_and_timezone(self):
        today = timezone.localdate()
        cutoff = today - relativedelta(months=6)
        boundary = timezone.make_aware(datetime.combine(cutoff, datetime.min.time()))
        self.scope.filter(pk=self.findings[0].pk).update(created=boundary - timedelta(seconds=1))
        self.scope.filter(pk=self.findings[1].pk).update(created=boundary, severity="Unknown")
        expected_rows = self.scope.filter(created__date__gte=cutoff).values("created__year", "created__month", "severity").annotate(count=Count("severity")).order_by()
        expected = {}
        severity_map = {"Critical": "a", "High": "b", "Medium": "c", "Low": "d", "Info": "e"}
        for row in expected_rows:
            key = f"{row['created__year']}-{row['created__month']:02}"
            stats = expected.setdefault(key, {"y": key, "a": 0, "b": 0, "c": 0, "d": 0, "e": 0, None: 0})
            stats[severity_map.get(row["severity"])] += row["count"]
        with CaptureQueriesContext(connection) as queries:
            actual = get_severities_by_month(self.scope, today)
        self.assertEqual(actual, [expected[key] for key in sorted(expected)])
        self.assertEqual(len(queries), 1)
        self.assertNotIn("EXTRACT(YEAR", queries[0]["sql"])

    def test_punchcard_reads_daily_aggregate_once(self):
        today = timezone.localdate()
        self.scope.update(created=timezone.now() - timedelta(days=1))
        with self.assertNumQueries(1):
            punchcard, ticks = get_punchcard_data(self.scope, today - relativedelta(weeks=26), 26)
        self.assertIsNotNone(ticks)
        self.assertEqual(sum(row[3] for row in punchcard), 3)
        with self.assertNumQueries(1):
            self.assertEqual(get_punchcard_data(self.scope.filter(pk=-1), today, 26), (None, None))

    def test_simple_metrics_aggregates_without_loading_finding_text(self):
        today = timezone.localdate()
        self.scope.update(verified=True, duplicate=False, false_p=False, out_of_scope=False, date=today)
        self.scope.filter(pk=self.findings[1].pk).update(severity="Unknown")
        self.scope.filter(pk=self.findings[2].pk).update(is_mitigated=True, mitigated=timezone.now())
        self.client.force_login(self.admin)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("simple_metrics"))
        self.assertEqual(response.status_code, 200)
        stats = response.context["findings"][self.product.prod_type]
        self.assertEqual(stats, {"Total": 3, "S0": 0, "S1": 1, "S2": 0, "S3": 0, "S4": 2, "Opened": 3, "Closed": 1})
        finding_queries = [q["sql"] for q in queries if 'FROM "dojo_finding"' in q["sql"]]
        self.assertTrue(finding_queries)
        self.assertTrue(all('"description"' not in sql for sql in finding_queries))
        self.scope.filter(pk=self.findings[0].pk).update(false_p=True)
        filtered = self.client.get(reverse("simple_metrics"))
        self.assertEqual(filtered.context["findings"][self.product.prod_type]["Total"], 2)
