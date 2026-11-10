from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils.timezone import now
from rest_framework.test import APITestCase

from dojo.models import (
    Dojo_User,
    DojoMeta,
    Engagement,
    Finding,
    Product,
    Product_Type,
    Regulation,
    Test,
    Test_Type,
)


class TestProductListNPlusOne(APITestCase):

    """
    Regression: the /api/v2/products/ and /api/v3/assets/ list endpoints must
    load all serialized relations in bulk so that the query count does not grow
    with the number of products in the response.

    Before the fix, each product triggered separate queries for tags,
    product_meta, authorized_users, regulations, and the active-finding count
    — a classic N+1. SlugRelatedField FKs and M2M/reverse-FK relations are
    loaded in bulk. API v2 also loads active finding IDs for the product page
    together and uses their lengths for the serialized counts.

    Each test asserts that the query count with 1 product is identical to the
    query count with 5 products, proving zero per-product query growth.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = Dojo_User.objects.create(
            username="prodprefetch_user", is_staff=True, is_superuser=True,
        )
        cls.prod_type = Product_Type.objects.create(name="ProdPrefetch PT")
        cls.test_type = Test_Type.objects.create(name="ProdPrefetch TT")
        cls.regulation = Regulation.objects.create(
            name="ProdPrefetch Reg", acronym="PPR", category="privacy",
            jurisdiction="international",
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)
        self.client.force_login(self.user)

    def _create_product(self, suffix, *, with_finding=True):
        """Create a product with every relation the serializer renders."""
        product = Product.objects.create(
            name=f"ProdPrefetch Product {suffix}",
            prod_type=self.prod_type,
            description="N+1 test product",
        )
        product.tags.add("prefetch-tag-a", "prefetch-tag-b")
        product.authorized_users.add(self.user)
        product.regulations.add(self.regulation)
        DojoMeta.objects.create(product=product, name="key", value="val")

        engagement = Engagement.objects.create(
            name=f"ProdPrefetch Eng {suffix}",
            product=product,
            target_start=now(),
            target_end=now(),
        )
        test = Test.objects.create(
            title=f"ProdPrefetch Test {suffix}",
            engagement=engagement,
            test_type=self.test_type,
            target_start=now(),
            target_end=now(),
        )
        if with_finding:
            self._create_finding(test, suffix)
        return product

    def _create_finding(self, test, suffix, *, active=True):
        return Finding.objects.create(
            title=f"ProdPrefetch Finding {suffix}",
            test=test,
            reporter=self.user,
            severity="High",
            active=active,
        )

    def _query_count(self, url):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content[:2000])
        return len(ctx.captured_queries)

    def _assert_constant_query_count(self, url):
        self._create_product("baseline")
        # Warm-up request: fills ContentType cache and other one-time lookups.
        self._query_count(url)
        with_one = self._query_count(url)

        extra_products = 4
        for i in range(extra_products):
            self._create_product(f"extra-{i}")
        with_five = self._query_count(url)

        self.assertEqual(with_five, with_one, f"{url}: query count grew with page size")

    def test_product_list_query_count_constant(self):
        self._assert_constant_query_count("/api/v2/products/")

    def test_product_page_uses_one_finding_query_for_ids_and_counts(self):
        empty = self._create_product("empty", with_finding=False)
        populated = self._create_product("populated", with_finding=False)
        other = self._create_product("outside page")
        test = Test.objects.get(engagement__product=populated)
        first = self._create_finding(test, "first")
        self._create_finding(test, "inactive", active=False)
        second = self._create_finding(test, "second")

        url = "/api/v2/products/"
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url, {"limit": 2, "o": "id"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 3)
        self.assertEqual(
            [(p["id"], p["findings_count"], p["findings_list"]) for p in data["results"]],
            [(empty.pk, 0, []), (populated.pk, 2, [first.pk, second.pk])],
        )
        self.assertIsNotNone(data["next"])
        finding_queries = [query["sql"] for query in queries if 'FROM "dojo_finding"' in query["sql"]]
        self.assertEqual(len(finding_queries), 1)
        self.assertNotIn("COUNT(", finding_queries[0].upper())

        next_page = self.client.get(url, {"limit": 2, "offset": 2, "o": "id"})
        self.assertEqual(next_page.status_code, 200)
        self.assertEqual([p["id"] for p in next_page.json()["results"]], [other.pk])
        detail = self.client.get(f"{url}{populated.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["findings_count"], 2)
        self.assertEqual(detail.json()["findings_list"], [first.pk, second.pk])

    def test_product_list_finding_ids_respect_product_access(self):
        visible = self._create_product("visible")
        hidden = self._create_product("hidden")
        reader = Dojo_User.objects.create_user(username="product_prefetch_reader")
        visible.authorized_users.add(reader)
        self.client.force_authenticate(user=reader)
        self.client.force_login(reader)

        response = self.client.get("/api/v2/products/", {"id": f"{visible.pk},{hidden.pk}"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        result, = data["results"]
        self.assertEqual(result["id"], visible.pk)
        self.assertEqual(result["findings_list"], visible.open_findings_list())
        self.assertEqual(result["findings_count"], 1)

    @classmethod
    def _v3_enabled(cls):
        from django.conf import settings  # noqa: PLC0415
        return getattr(settings, "V3_FEATURE_LOCATIONS", False)

    def test_asset_list_query_count_constant(self):
        if not self._v3_enabled():
            self.skipTest("V3_FEATURE_LOCATIONS is disabled")
        self._assert_constant_query_count("/api/v3/assets")
