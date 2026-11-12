from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test.utils import CaptureQueriesContext

from dojo.finding.queries import get_authorized_findings_for_queryset
from dojo.models import Dojo_User, Engagement, Finding, Product, Product_Type, Test
from unittests import test_round4_performance as round4
from unittests.dojo_test_case import DojoTestCase, versioned_fixtures


@versioned_fixtures
class TestRC3FindingScope(DojoTestCase):
    fixtures = ["dojo_testdata.json"]
    setUp = round4.TestRound4Performance.setUp

    def test_direct_membership_preserves_exact_count_and_caller_filter(self):
        scope = Finding.objects.filter(active=True).order_by("-pk")
        expected = sorted((finding.pk for finding in self.findings[:2]), reverse=True)
        with CaptureQueriesContext(connection) as queries:
            actual = list(get_authorized_findings_for_queryset("view", scope, self.reader).values_list("pk", flat=True))
        self.assertEqual(actual, expected)
        self.assertEqual(len(queries), 1)
        # The Finding heap must not be joined to Test for each matching Test.
        self.assertNotIn('"dojo_finding"."test_id" = "dojo_test"."id"', queries[0]["sql"])
        self.assertEqual(get_authorized_findings_for_queryset("view", scope, self.reader).count(), 2)

    def test_product_type_and_overlapping_memberships_do_not_duplicate_findings(self):
        self.product.prod_type.authorized_users.add(self.reader)
        self.product.authorized_users.add(Dojo_User.objects.get(username="user1"))
        test = self.findings[0].test
        engagement = Engagement.objects.create(product=self.other, target_start=test.engagement.target_start, target_end=test.engagement.target_end)
        other_test = Test.objects.create(engagement=engagement, test_type=test.test_type, target_start=test.target_start, target_end=test.target_end)
        hidden = Finding.objects.create(test=other_test, title="type membership", severity="High")
        result = list(get_authorized_findings_for_queryset("view", None, user=self.reader).order_by("pk").values_list("pk", flat=True))
        self.assertEqual(result, sorted([finding.pk for finding in self.findings] + [hidden.pk]))

    def test_missing_membership_and_privileged_action_stay_denied(self):
        outsider = Dojo_User.objects.create(username="rc3_outsider")
        for user, permission in ((outsider, "view"), (self.reader, "delete"), (AnonymousUser(), "view")):
            with self.subTest(user=user, permission=permission):
                self.assertFalse(get_authorized_findings_for_queryset(permission, None, user=user).exists())

    def test_staff_and_superuser_keep_supplied_queryset(self):
        scope = self.scope.filter(pk=self.findings[0].pk)
        self.reader.is_staff = True
        for user in (self.reader, self.admin):
            with self.subTest(user=user):
                self.assertEqual(list(get_authorized_findings_for_queryset("delete", scope, user)), list(scope))

    def test_membership_removal_takes_effect_on_new_query(self):
        self.assertEqual(get_authorized_findings_for_queryset("view", None, user=self.reader).count(), 3)
        self.product.authorized_users.remove(self.reader)
        self.assertEqual(get_authorized_findings_for_queryset("view", None, user=self.reader).count(), 0)

    def test_foreign_product_filter_cannot_widen_scope(self):
        foreign_type = Product_Type.objects.create(name="rc3 foreign type", description="RC3 scope fixture")
        foreign_product = Product.objects.create(name="rc3 foreign", description="RC3 scope fixture", prod_type=foreign_type)
        self.assertFalse(get_authorized_findings_for_queryset("view", None, user=self.reader).filter(test__engagement__product=foreign_product).exists())
