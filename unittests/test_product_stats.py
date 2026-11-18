"""Behavioral Product Stats regression oracles, run unchanged on RC4 and candidate."""
import json
from datetime import UTC, date, datetime
from pathlib import Path

from django.db import connection
from django.test.utils import CaptureQueriesContext

from dojo.metrics.views import _product_stats  # noqa: PLC2701 -- regression of internal aggregation helper
from dojo.models import Engagement, Finding, Product, Product_Type, Test, Test_Type, User
from dojo.product.queries import get_authorized_products
from unittests.dojo_test_case import DojoTestCase


class ProductStats(DojoTestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username="rc5_stats_admin", password="test")  # noqa: S106 -- fixture user
        pt = Product_Type.objects.create(name="RC5 stats")
        self.products = []
        self.tests = []
        tt, _ = Test_Type.objects.get_or_create(name="Manual")
        for name in ("Allowed <one>", "Other"):
            product = Product.objects.create(name=name, prod_type=pt, description="RC5")
            engagement = Engagement.objects.create(name="RC5", product=product, target_start=date(2024, 1, 1), target_end=date(2024, 12, 31))
            test = Test.objects.create(engagement=engagement, test_type=tt, target_start=datetime(2024, 1, 1, tzinfo=UTC), target_end=datetime(2024, 12, 31, tzinfo=UTC))
            self.products.append(product)
            self.tests.append(test)

    def add(self, n, index=0, severity="High", **kw):
        Finding.objects.bulk_create([Finding(title="RC5", test=self.tests[index], severity=severity, active=True, reporter=self.user, **kw) for _ in range(n)], batch_size=1000)

    def table(self, products=None):
        with CaptureQueriesContext(connection) as captured:
            result = _product_stats(products if products is not None else Product.objects.filter(pk__in=[p.pk for p in self.products]))
        out = Path("/tmp/rc5-evidence")
        out.mkdir(exist_ok=True)
        (out / (self._testMethodName + ".json")).write_text(json.dumps({"tables": result, "sql": [q["sql"] for q in captured]}, indent=2))
        return result

    def test_multiple_findings_per_product(self):
        self.add(3)
        self.add(4, index=1, severity="Critical")
        top, total = self.table()
        self.assertEqual([r[-1] for r in top], [4, 3])
        self.assertEqual([r[-1] for r in total], [3, 4])
        self.assertEqual(total[0][1:], [0, 3, 0, 0, 3])
        self.assertIn("&lt;one&gt;", total[0][0])

    def test_empty(self):
        self.assertEqual(self.table(), ([], []))

    def test_statuses_and_scope(self):
        self.add(2)
        self.add(9, index=1)
        self.add(3, is_mitigated=True, mitigated=datetime(2024, 4, 1, tzinfo=UTC))
        self.add(2)
        ids = list(Finding.objects.filter(test=self.tests[0]).order_by("-id").values_list("pk", flat=True)[:2])
        Finding.objects.filter(pk__in=ids).update(active=False)
        top, total = self.table(Product.objects.filter(pk=self.products[0].pk))
        self.assertEqual(len(total), 1)
        self.assertEqual(total[0][-1], 2)
        self.assertEqual(top, total)

    def test_large_exact(self):
        self.add(12003)
        self.add(10000, index=1)
        top, total = self.table()
        self.assertEqual([r[-1] for r in total], [12003, 10000])
        self.assertEqual([r[-1] for r in top], [12003, 10000])

    def test_product_rbac(self):
        user = User.objects.create(username="rc5_stats_member")
        self.products[0].authorized_users.add(user.pk)
        self.add(3)
        self.add(9, index=1)
        _, total = self.table(get_authorized_products("view", user=user))
        self.assertEqual(len(total), 1)
        self.assertEqual(total[0][-1], 3)
        self.products[0].authorized_users.remove(user.pk)
        self.assertEqual(self.table(get_authorized_products("view", user=user)), ([], []))
