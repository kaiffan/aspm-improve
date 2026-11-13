from itertools import product

from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from dojo.filters import cwe_options
from dojo.finding.queries import get_authorized_findings_for_queryset
from dojo.models import Dojo_User, Engagement, Finding, Notes, Test, Test_Type
from dojo.utils import Product_Tab
from unittests import test_round4_performance as round4
from unittests.dojo_test_case import DojoTestCase, versioned_fixtures


@versioned_fixtures
class TestFinalHardening(DojoTestCase):
    fixtures = ["dojo_testdata.json"]
    setUp = round4.TestRound4Performance.setUp

    def choices_fixture(self):
        test = self.findings[0].test
        rows = Finding.objects.bulk_create([
            Finding(test=test, title=f"Hardening CWE {i}", severity="High", cwe=value, active=True)
            for i, value in enumerate([None, 0, -1, 79, 22, 79, 999999])
        ])
        return Finding.objects.filter(pk__in=[row.pk for row in rows]), rows

    def test_cwe_options_preserve_null_empty_unknown_and_numeric_order(self):
        queryset, _ = self.choices_fixture()
        with CaptureQueriesContext(connection) as queries:
            values = cwe_options(queryset.order_by("-title"))
        self.assertEqual(values, [(22, 22), (79, 79), (999999, 999999)])
        self.assertEqual(len(queries), 1)
        self.assertNotIn('"description"', queries[0]["sql"])
        self.assertEqual(cwe_options(queryset.none()), [])

    def test_cwe_options_preserve_product_and_privileged_role_scopes(self):
        queryset, rows = self.choices_fixture()
        now = timezone.now()
        engagement = Engagement.objects.create(product=self.other, name="CWE foreign", target_start=now.date(), target_end=now.date())
        other_test = Test.objects.create(engagement=engagement, test_type=Test_Type.objects.first(), target_start=now, target_end=now)
        hidden = Finding.objects.bulk_create([Finding(test=other_test, title="Hidden CWE", cwe=9421, severity="High")])[0]
        queryset = Finding.objects.filter(pk__in=[row.pk for row in rows] + [hidden.pk])
        for hinted in [False, True]:
            scoped = get_authorized_findings_for_queryset("view", queryset, self.reader, prefer_product_join=hinted)
            self.assertEqual(cwe_options(scoped), [(22, 22), (79, 79), (999999, 999999)])
        admin_scope = get_authorized_findings_for_queryset("view", queryset, self.admin)
        self.assertEqual(cwe_options(admin_scope), [(22, 22), (79, 79), (9421, 9421), (999999, 999999)])
        outsider = Dojo_User.objects.create(username="hardening_outsider")
        for user in [outsider, AnonymousUser()]:
            self.assertEqual(cwe_options(get_authorized_findings_for_queryset("view", queryset, user)), [])
        self.product.prod_type.authorized_users.add(self.reader)
        self.assertEqual(cwe_options(get_authorized_findings_for_queryset("view", queryset, self.reader)), [(22, 22), (79, 79), (9421, 9421), (999999, 999999)])

    def test_cwe_options_deduplicate_related_join_fanout(self):
        queryset, rows = self.choices_fixture()
        notes = [Notes.objects.create(entry=f"CWE note {i}", author=self.admin, date=timezone.now()) for i in range(2)]
        rows[3].notes.add(*notes)
        joined = queryset.filter(notes__in=notes)
        self.assertEqual(joined.count(), 2)
        self.assertEqual(cwe_options(joined), [(79, 79)])

    def test_cwe_options_preserve_existing_filters(self):
        queryset, rows = self.choices_fixture()
        queryset.filter(pk=rows[-1].pk).update(active=False)
        self.assertEqual(cwe_options(queryset.filter(active=True, cwe__gte=79)), [(79, 79)])
        self.assertEqual(cwe_options(queryset.filter(active=False)), [(999999, 999999)])

    def test_open_count_remains_exact_for_every_predicate_combination(self):
        self.scope.update(active=False)
        test = self.findings[0].test
        rows = []
        for i, flags in enumerate(product([False, True], repeat=5)):
            active, false_p, duplicate, out_of_scope, mitigated = flags
            rows.append(Finding(test=test, title=f"Hardening flags {i}", severity="Low", active=active,
                                false_p=false_p, duplicate=duplicate, out_of_scope=out_of_scope,
                                mitigated=timezone.now() if mitigated else None, verified=False))
        Finding.objects.bulk_create(rows)
        with CaptureQueriesContext(connection) as queries:
            tab = Product_Tab(self.product)
            self.assertEqual(tab.open_findings_count, 1)
            self.assertEqual(tab.open_findings_count, 1)
        self.assertEqual(len(queries), 1)

    def test_cwe_index_covers_id_exclusion_without_changing_result_columns(self):
        indexes = {index.name: index for index in Finding._meta.indexes}
        self.assertIn("idx_finding_test_cwe_cover", indexes)
        index = indexes["idx_finding_test_cwe_cover"]
        self.assertEqual(index.fields, ["test", "cwe"])
        self.assertEqual(index.include, ("id",))

    def test_open_index_predicate_matches_exact_count_contract(self):
        indexes = {index.name: index for index in Finding._meta.indexes}
        self.assertIn("idx_finding_open_test", indexes)
        index = indexes["idx_finding_open_test"]
        self.assertEqual(index.fields, ["test"])
        self.assertEqual(dict(index.condition.children), {"active": True, "duplicate": False, "false_p": False,
                                                          "out_of_scope": False, "mitigated__isnull": True})
