from django.urls import reverse

from dojo.finding.ui.filters import FindingFilterWithoutObjectLookups
from dojo.models import Finding
from unittests import test_round4_performance as round4
from unittests.dojo_test_case import DojoTestCase, versioned_fixtures


@versioned_fixtures
class RC2ProductFilterTests(DojoTestCase):
    fixtures = ["dojo_testdata.json"]

    def setUp(self):
        round4.TestRound4Performance.setUp(self)
        self.client.force_login(self.reader)

    def get_page(self, **params):
        response = self.client.get(reverse("open_findings"), params)
        self.assertEqual(response.status_code, 200)
        return response

    def test_product_choices_are_authorized(self):
        response = self.get_page()
        form = response.context["filtered"].form
        products = list(form.fields["test__engagement__product"].queryset.values_list("pk", flat=True))
        self.assertIn(self.product.pk, products)
        self.assertNotIn(self.other.pk, products)

    def test_combined_product_severity_active_and_empty_result(self):
        response = self.get_page(test__engagement__product=self.product.pk, severity="High", active="2")
        self.assertEqual([f.pk for f in response.context["findings"]], [self.findings[0].pk])
        empty = self.get_page(test__engagement__product=self.product.pk, severity="Critical")
        self.assertEqual(list(empty.context["findings"]), [])

    def test_pages_and_sort_keep_product_scope_without_duplicates(self):
        ids = []
        for number in (1, 2):
            response = self.get_page(test__engagement__product=self.product.pk, page=number, page_size=1, o="severity")
            page = response.context["findings"]
            ids.extend(f.pk for f in page)
            self.assertEqual(page.paginator.count, 2)
            self.assertContains(response, f"test__engagement__product={self.product.pk}")
        self.assertEqual(len(set(ids)), 2)
        self.assertEqual(set(ids), {f.pk for f in self.findings[:2]})

    def test_unowned_and_nonexistent_scope_never_expose_foreign_findings(self):
        for product in (self.other.pk, 999999999):
            response = self.get_page(test__engagement__product=product)
            self.assertTrue(all(f.test.engagement.product_id == self.product.pk for f in response.context["findings"]))

    def test_context_product_cannot_be_overridden(self):
        response = self.client.get(reverse("product_open_findings", args=[self.product.pk]), {"test__engagement__product": self.other.pk})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(f.test.engagement.product_id == self.product.pk for f in response.context["findings"]))
        denied = self.client.get(reverse("product_open_findings", args=[self.other.pk]))
        self.assertIn(denied.status_code, (400, 403, 404))

    def test_supported_name_matching_uses_scoped_queryset(self):
        scope = Finding.objects.filter(test__engagement__product=self.product)
        for field in ("test__engagement__product__name", "test__engagement__product__name_contains"):
            filtered = FindingFilterWithoutObjectLookups({field: self.product.name}, queryset=scope, user=self.reader)
            self.assertEqual(set(filtered.qs.values_list("pk", flat=True)), set(self.scope.values_list("pk", flat=True)))
