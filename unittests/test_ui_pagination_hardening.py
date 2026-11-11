from django.http import QueryDict
from django.test import RequestFactory

from dojo.models import Product, Product_Type
from dojo.templatetags.navigation_tags import url_replace
from dojo.utils import get_page_items, get_page_items_and_count
from unittests.dojo_test_case import DojoTestCase


class UIPaginationHardeningTests(DojoTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        product_type = Product_Type.objects.create(name="Pagination")
        self.products = [Product.objects.create(name=f"Product {index}", description="Pagination", prod_type=product_type) for index in range(7)]

    def page(self, query="", queryset=None, prefix=""):
        if queryset is None:
            queryset = Product.objects.filter(pk__in=[p.pk for p in self.products]).order_by("description")
        return get_page_items(self.factory.get("/asset?" + query), queryset, 2, prefix=prefix)

    def test_tied_order_gets_unique_final_key_before_slice(self):
        page = self.page()
        self.assertEqual(page.object_list.query.order_by, ("description", "pk"))
        first = list(page.object_list.values_list("pk", flat=True))
        second = list(self.page("page=2").object_list.values_list("pk", flat=True))
        self.assertEqual(first + second, [p.pk for p in self.products[:4]])

    def test_explicit_unique_order_is_preserved(self):
        qs = Product.objects.filter(pk__in=[p.pk for p in self.products]).order_by("-pk")
        self.assertEqual(list(self.page(queryset=qs)), self.products[-1:-3:-1])
        self.assertEqual(self.page(queryset=qs).object_list.query.order_by, ("-pk",))

    def test_invalid_page_sizes_fall_back(self):
        for size in ("bad", "", "0", "-1"):
            with self.subTest(size=size):
                self.assertEqual(len(self.page("page_size=" + size)), 2)

    def test_page_size_is_bounded_without_materializing_queryset(self):
        page = self.page("page_size=1000000")
        self.assertEqual(page.paginator.per_page, 250)
        self.assertIsNone(page.object_list._result_cache)

    def test_page_number_edge_cases(self):
        for value, expected in (("", 1), ("bad", 1), ("-1", 4), ("0", 4), ("999999999999999999999", 4)):
            with self.subTest(value=value):
                self.assertEqual(self.page("page=" + value).number, expected)
        self.assertEqual(self.page().number, 1)
        self.assertEqual(self.page(queryset=Product.objects.none()).number, 1)

    def test_prefix_and_total_count(self):
        request = self.factory.get("/asset?closed_page=2&closed_page_size=3")
        page = get_page_items_and_count(request, Product.objects.order_by("description"), 2, prefix="closed_")
        self.assertEqual(page.number, 2)
        self.assertEqual(page.paginator.per_page, 3)
        self.assertEqual(page.total_count, 7)

    def test_lists_and_already_evaluated_queryset_keep_objects(self):
        self.assertEqual(list(self.page(queryset=self.products)), self.products[:2])
        qs = Product.objects.order_by("description")
        original = list(qs)
        original[0].temporary_annotation = "retained"
        self.assertEqual(self.page(queryset=qs)[0].temporary_annotation, "retained")

    def test_values_and_random_order_are_not_rewritten(self):
        for qs in (Product.objects.values("name").distinct(), Product.objects.order_by("?")):
            self.assertEqual(self.page(queryset=qs).object_list.query.order_by, qs.query.order_by)

    def test_paging_links_preserve_multivalued_filters_and_sort(self):
        request = self.factory.get("/finding/open")
        request.GET = QueryDict("severity=High&severity=Critical&test__engagement__product=1&o=-date&page=3")
        updated = QueryDict(url_replace(request, "page", 4))
        self.assertEqual(updated.getlist("severity"), ["High", "Critical"])
        self.assertEqual(updated["test__engagement__product"], "1")
        self.assertEqual(updated["o"], "-date")
        self.assertEqual(updated["page"], "4")
