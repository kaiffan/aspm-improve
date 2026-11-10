from django.urls import include, path, reverse
from django.utils import timezone
from rest_framework.routers import SimpleRouter
from rest_framework.test import APIClient

from dojo.models import Dojo_User, Engagement, Finding, Product, Test, Test_Type
from dojo.scm.api.urls import add_scm_urls
from dojo.scm.models import Commit, Repository
from dojo.scm.ui.urls import urlpatterns as scm_urls
from unittests.dojo_test_case import DojoTestCase, versioned_fixtures

router = SimpleRouter()
add_scm_urls(router)
urlpatterns = [path("api/v2/", include(router.urls)), *scm_urls, path("", include("dojo.urls"))]


@versioned_fixtures
class SCMSurfacesTest(DojoTestCase):
    fixtures = ["dojo_testdata.json"]

    def setUp(self):
        super().setUp()
        self.enterContext(self.settings(ASPM_SCM_HIERARCHY=True, ROOT_URLCONF=__name__))
        self.admin = self.get_test_admin()
        self.member = Dojo_User.objects.create_user(username="scm_product_member")
        self.product, self.other_product = Product.objects.order_by("pk")[:2]
        self.product.authorized_users.add(self.member)
        self.api = APIClient()
        self.api.force_authenticate(self.member)
        self.client.force_login(self.member)

    def test_api_canonicalizes_and_guards_repository_identity(self):
        list_url = reverse("repository-list")
        canonical = "https://example.invalid/team/main"
        data = {"product": self.product.pk, "url": "https://EXAMPLE.invalid:443/team/main.git/", "provider": "other"}
        response = self.api.post(list_url, data, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["url"], canonical)
        detail_url = reverse("repository-detail", args=(response.data["id"],))

        duplicate = self.api.post(list_url, {**data, "url": canonical}, format="json")
        self.assertEqual(duplicate.status_code, 400, duplicate.data)
        self.assertEqual(self.api.patch(detail_url, {"url": "https://example.invalid/team/other"}, format="json").status_code, 400)
        self.assertEqual(self.api.patch(detail_url, {"metadata": []}, format="json").status_code, 400)
        self.assertEqual(self.api.patch(detail_url, {"default_branch": "release"}, format="json").status_code, 200)
        self.assertEqual(self.api.delete(detail_url).status_code, 403)

    def test_api_commit_creation_validates_sha_parents_and_identity(self):
        repository = Repository.objects.create(product=self.product, url="https://example.invalid/project")
        list_url = reverse("commit-list")
        data = {"repository": repository.pk, "sha": "A" * 40, "parent_shas": ["B" * 40]}
        response = self.api.post(list_url, data, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["sha"], "a" * 40)
        self.assertEqual(response.data["parent_shas"], ["b" * 40])
        self.assertEqual(self.api.post(list_url, data, format="json").status_code, 400)
        self.assertEqual(self.api.post(list_url, {**data, "sha": "ab123"}, format="json").status_code, 400)
        detail_url = reverse("commit-detail", args=(response.data["id"],))
        other_repository = Repository.objects.create(product=self.product, url="https://example.invalid/other")
        self.assertEqual(self.api.patch(detail_url, {"sha": "c" * 40}, format="json").status_code, 400)
        self.assertEqual(self.api.patch(detail_url, {"repository": other_repository.pk}, format="json").status_code, 400)
        self.assertEqual(self.api.patch(detail_url, {"parent_shas": ["invalid"]}, format="json").status_code, 400)
        self.assertEqual(self.api.patch(detail_url, {"message": "Updated"}, format="json").status_code, 200)
        self.assertEqual(self.api.get(list_url, {"product": self.product.pk}).data["count"], 1)
        self.api.force_authenticate(self.admin)
        self.assertEqual(self.api.delete(detail_url).status_code, 204)

    def test_outside_product_objects_cannot_be_viewed_or_used_as_parents(self):
        repository = Repository.objects.create(product=self.other_product, url="https://example.invalid/foreign")
        commit = Commit.objects.create(repository=repository, sha="a" * 40)
        self.assertEqual(self.api.get(reverse("repository-detail", args=(repository.pk,))).status_code, 404)
        self.assertEqual(self.api.get(reverse("commit-detail", args=(commit.pk,))).status_code, 404)
        self.assertEqual(self.client.get(reverse("scm_repository_detail", args=(repository.pk,))).status_code, 404)
        self.assertEqual(self.client.get(reverse("scm_commit_detail", args=(commit.pk,))).status_code, 404)
        list_url = reverse("commit-list")
        hidden = self.api.get(list_url, {"repository": repository.pk})
        missing = self.api.get(list_url, {"repository": repository.pk + 10_000})
        self.assertEqual((hidden.status_code, missing.status_code), (200, 200))
        self.assertEqual((hidden.data["count"], missing.data["count"]), (0, 0))
        self.assertEqual(self.api.post(list_url, {"repository": repository.pk, "sha": "b" * 40}, format="json").status_code, 400)
        self.assertEqual(self.api.post(reverse("repository-list"), {
            "product": self.other_product.pk, "url": "https://example.invalid/new",
        }, format="json").status_code, 400)

    def test_moving_an_engagement_preserves_legacy_fields_and_detaches_commit(self):
        repository = Repository.objects.create(product=self.product, url="https://example.invalid/source")
        commit = Commit.objects.create(repository=repository, sha="a" * 40)
        today = timezone.localdate()
        engagement, = Engagement.objects.bulk_create([
            Engagement(
                product=self.product, name="SCM move", target_start=today, target_end=today,
                commit=commit, commit_hash=commit.sha, source_code_management_uri=repository.url,
            ),
        ])
        self.api.force_authenticate(self.admin)
        detail = reverse("engagement-detail", args=(engagement.pk,))
        self.assertEqual(self.api.get(detail).data["commit"], commit.pk)
        response = self.api.patch(detail, {"product": self.other_product.pk}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIsNone(response.data["commit"])
        engagement.refresh_from_db()
        self.assertEqual(engagement.product_id, self.other_product.pk)
        self.assertIsNone(engagement.commit_id)
        self.assertEqual(engagement.commit_hash, commit.sha)
        self.assertEqual(engagement.source_code_management_uri, repository.url)

    def test_comparison_groups_findings_and_rejects_another_repository(self):
        repository = Repository.objects.create(product=self.product, url="https://example.invalid/comparison")
        base, target = Commit.objects.bulk_create([
            Commit(repository=repository, sha="a" * 40), Commit(repository=repository, sha="b" * 40),
        ])
        now = timezone.now()
        engagements = Engagement.objects.bulk_create([
            Engagement(product=self.product, commit=commit, name=f"Engagement {commit.pk}", target_start=now.date(), target_end=now.date())
            for commit in (base, target)
        ])
        scanner = Test_Type.objects.order_by("pk").first()
        previous_test, target_test = Test.objects.bulk_create([
            Test(engagement=engagement, test_type=scanner, target_start=now, target_end=now)
            for engagement in engagements
        ])
        Finding.objects.bulk_create([
            Finding(test=test, title=title, hash_code=fingerprint, severity="High", numerical_severity="S1", reporter=self.admin)
            for test, title, fingerprint in (
                (previous_test, "Previous shared", "shared"), (previous_test, "Previous fixed", "fixed"),
                (target_test, "Current shared", "shared"), (target_test, "Current duplicate", "shared"),
                (target_test, "Current new", "new"),
            )
        ])
        product_url = reverse("scm_repository_list", args=(self.product.pk,))
        self.assertContains(self.client.get(product_url), reverse("scm_repository_detail", args=(repository.pk,)))
        self.assertContains(self.client.get(reverse("scm_repository_detail", args=(repository.pk,))), reverse("scm_commit_detail", args=(target.pk,)))
        self.assertContains(self.client.get(reverse("scm_commit_detail", args=(target.pk,))), reverse("view_engagement", args=(engagements[-1].pk,)))
        comparison_url = reverse("scm_commit_compare", args=(target.pk,))
        for category, title in (("new", "Current new"), ("fixed", "Previous fixed"), ("unchanged", "Current shared")):
            with self.subTest(category=category):
                response = self.client.get(comparison_url, {"base": base.pk, "category": category})
                self.assertEqual(response.status_code, 200)
                self.assertEqual([finding.title for finding in response.context["findings"]], [title])
        other_repository = Repository.objects.create(product=self.product, url="https://example.invalid/another")
        other_commit = Commit.objects.create(repository=other_repository, sha="c" * 40)
        self.assertEqual(self.client.get(comparison_url, {"base": other_commit.pk}).status_code, 404)
