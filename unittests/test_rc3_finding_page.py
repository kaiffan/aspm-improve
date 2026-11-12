from unittest.mock import patch

from django.db import connection
from django.test import RequestFactory, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from dojo.finding.queries import prefetch_for_findings
from dojo.models import Finding, Risk_Acceptance
from dojo.utils import get_page_items, get_words_for_field
from unittests import test_round4_performance as round4
from unittests.dojo_test_case import DojoTestCase, versioned_fixtures


@versioned_fixtures
class TestRC3FindingPage(DojoTestCase):
    fixtures = ["dojo_testdata.json"]
    setUp = round4.TestRound4Performance.setUp

    def test_annotations_hydrate_only_the_selected_ordered_page(self):
        for order in ("pk", "-pk", "numerical_severity"):
            with self.subTest(order=order):
                queryset = self.scope.order_by(order)
                page = get_page_items(RequestFactory().get("/?page=2&page_size=1"), queryset, 25)
                expected = list(page.object_list.values_list("pk", flat=True))
                with CaptureQueriesContext(connection) as queries:
                    actual = list(prefetch_for_findings(page.object_list))
                self.assertEqual([finding.pk for finding in actual], expected)
                self.assertEqual(page.paginator.count, 3)
                self.assertIn(" IN (SELECT ", queries[0]["sql"])
                self.assertIn("LIMIT 1 OFFSET 1", queries[0]["sql"])
                self.assertEqual(list(queryset.values_list("pk", flat=True)), list(self.scope.order_by(order).values_list("pk", flat=True)))

    def test_test_page_retains_count_filters_and_denial(self):
        self.client.force_login(self.reader)
        test = self.findings[0].test
        for page in (1, 2, 3):
            response = self.client.get(reverse("view_test", args=[test.pk]), {"findingspage_size": 1, "findingspage": page})
            self.assertEqual(response.status_code, 200)
            actual = response.context["findings"]
            self.assertEqual(actual.paginator.count, 3)
            self.assertEqual(len(list(actual)), 1)
            self.assertEqual(actual[0].test_id, test.pk)
        foreign = Finding.objects.exclude(test__engagement__product=self.product).first()
        if foreign is not None:
            self.assertIn(self.client.get(reverse("view_test", args=[foreign.test_id])).status_code, (400, 403, 404))

    def test_evaluated_and_unsliced_collections_keep_existing_behavior(self):
        findings = list(self.scope.order_by("pk"))
        self.assertIs(prefetch_for_findings(findings), findings)
        self.assertEqual([finding.pk for finding in prefetch_for_findings(self.scope.order_by("pk"))], [finding.pk for finding in findings])

    def test_related_ordering_retains_original_page_cardinality(self):
        for day in (1, 2):
            acceptance = Risk_Acceptance.objects.create(name=f"RC3 acceptance {day}", owner=self.admin)
            Risk_Acceptance.objects.filter(pk=acceptance.pk).update(created=timezone.now().replace(day=day))
            acceptance.accepted_findings.add(self.findings[0])
        ordered = self.scope.filter(pk=self.findings[0].pk).order_by("risk_acceptance__created__date", "pk")
        expected = list(prefetch_for_findings(ordered)[:1])
        actual = list(prefetch_for_findings(ordered[:1]))
        self.assertEqual([finding.pk for finding in actual], [finding.pk for finding in expected])

    def test_multivalued_filter_retains_page_boundary(self):
        acceptances = [Risk_Acceptance.objects.create(name=f"RC3 filter {index}", owner=self.admin) for index in range(2)]
        acceptances[0].accepted_findings.add(*self.findings[:2])
        acceptances[1].accepted_findings.add(self.findings[0])
        ordered = self.scope.filter(risk_acceptance__in=acceptances).order_by("pk")
        expected = list(prefetch_for_findings(ordered)[1:2])
        actual = list(prefetch_for_findings(ordered[1:2]))
        self.assertEqual([finding.pk for finding in actual], [finding.pk for finding in expected])

    @override_settings(MAX_AUTOCOMPLETE_WORDS=1)
    def test_capped_autocomplete_projects_only_authorized_values(self):
        self.scope.update(title="rc3visible needle")
        with patch("dojo.utils.get_current_user", return_value=self.reader), CaptureQueriesContext(connection) as queries:
            words = get_words_for_field(Finding, "title")
        self.assertEqual(words, ["needle", "rc3visible"])
        self.assertEqual(len(queries), 1)
        self.assertIn("OFFSET 0", queries[0]["sql"])
        self.product.authorized_users.remove(self.reader)
        with patch("dojo.utils.get_current_user", return_value=self.reader):
            self.assertEqual(get_words_for_field(Finding, "title"), [])
