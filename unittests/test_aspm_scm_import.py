import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, connections
from django.test import SimpleTestCase, override_settings, skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from dojo.importers.auto_create_context import AutoCreateContextManager
from dojo.models import Development_Environment, Engagement, Product, Product_Type, Test
from dojo.scm.imports import materialize_scm_scan, resolve_scm_scan
from dojo.scm.models import Commit, Repository
from dojo.url.models import URL

SHA = "a" * 40
REPO_URL = "https://github.com/example/scm-import"


@override_settings(ASPM_SCM_HIERARCHY=True)
class TestSCMScanImport(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.member = user_model.objects.create_user(username="aspm-scm-import-member")
        product_type, = Product_Type.objects.bulk_create([Product_Type(name="SCM import product type")])
        cls.product, cls.hidden = Product.objects.bulk_create([
            Product(name="SCM import product", description="Visible", prod_type=product_type),
            Product(name="SCM hidden product", description="Hidden", prod_type=product_type),
        ])
        cls.product.authorized_users.add(cls.member.pk)
        Development_Environment.objects.get_or_create(name="Development")

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.member)

    def scan(self, *, reimport=False, legacy=False, **changes):
        report = json.dumps({"findings": [{
            "title": "Synthetic SCM finding", "description": "Synthetic test report", "severity": "High",
        }]}).encode()
        payload = {
            "scan_type": "Generic Findings Import",
            "deduplication_execution_mode": "sync",
            "file": SimpleUploadedFile("scan.json", report, content_type="application/json"),
            "product_name": self.product.name,
            "repository_url": f"{REPO_URL}.git",
            "commit_hash": SHA.upper(),
            "branch_tag": "main",
            "test_title": "SCM scan",
            **changes,
        }
        if legacy:
            payload.pop("repository_url")
        return self.client.post(reverse("reimportscan-list" if reimport else "importscan-list"), payload, format="multipart")

    def assert_created(self, response):
        self.assertEqual(response.status_code, 201, response.content[:1000])
        return response.json()

    def assert_repository_count(self, expected):
        self.assertEqual(Repository.objects.filter(product__in=(self.product, self.hidden)).count(), expected)

    def assert_commit_count(self, expected):
        self.assertEqual(Commit.objects.filter(repository__product__in=(self.product, self.hidden)).count(), expected)

    def test_import_reuses_commit_engagement_and_reimport_finds_its_latest_test(self):
        first = self.assert_created(self.scan())
        second = self.assert_created(self.scan(repository_url=REPO_URL))
        self.assertEqual(first["engagement_id"], second["engagement_id"])
        self.assertNotEqual(first["test_id"], second["test_id"])
        third = self.assert_created(self.scan(reimport=True))
        self.assertEqual(third["test_id"], second["test_id"])
        self.assertNotIn("repository_url", third)

        repository = Repository.objects.get(product=self.product)
        commit = Commit.objects.get(repository=repository)
        engagement = Engagement.objects.get(commit=commit)
        self.assertEqual(repository.url, REPO_URL)
        self.assertEqual(repository.provider, Repository.Provider.GITHUB)
        self.assertEqual(commit.sha, SHA)
        self.assertEqual(commit.branch, "main")
        self.assertEqual(engagement.source_code_management_uri, REPO_URL)
        self.assertEqual(engagement.commit_hash, SHA)
        self.assertEqual(Test.objects.get(pk=third["test_id"]).commit_hash, SHA)

    def test_reimport_can_create_test_and_different_commit_gets_its_own_engagement(self):
        first = self.assert_created(self.scan(reimport=True, auto_create_context=True))
        second = self.assert_created(self.scan(reimport=True, auto_create_context=True, commit_hash="b" * 40))
        self.assertNotEqual(first["engagement_id"], second["engagement_id"])
        self.assert_repository_count(1)
        self.assert_commit_count(2)
        self.assertEqual(Engagement.objects.filter(product=self.product).count(), 2)

    def test_reimport_with_missing_test_creates_no_scm_context(self):
        response = self.scan(reimport=True)
        self.assertEqual(response.status_code, 400, response.content[:1000])
        self.assert_repository_count(0)
        self.assertFalse(Engagement.objects.filter(product=self.product).exists())

    def test_engagement_name_selects_a_named_engagement_within_the_commit(self):
        first = self.assert_created(self.scan(engagement_name="Scanner one"))
        second = self.assert_created(self.scan(engagement_name="Scanner two"))
        reimported = self.assert_created(self.scan(reimport=True, engagement_name="Scanner two"))
        self.assertNotEqual(first["engagement_id"], second["engagement_id"])
        self.assertEqual(reimported["test_id"], second["test_id"])
        self.assert_commit_count(1)

    def test_foreign_product_and_conflicting_explicit_test_are_rejected(self):
        self.assertEqual(self.scan(product_name=self.hidden.name).status_code, 403)
        self.assert_repository_count(0)
        created = self.assert_created(self.scan())
        response = self.scan(reimport=True, test=created["test_id"], commit_hash="b" * 40)
        self.assertEqual(response.status_code, 400, response.content[:1000])
        self.assert_commit_count(1)

    def test_existing_engagement_can_be_linked_and_conflicting_repository_is_refused(self):
        day = timezone.localdate()
        engagement, = Engagement.objects.bulk_create([
            Engagement(product=self.product, name="Legacy CI", target_start=day, target_end=day),
        ])
        created = self.assert_created(self.scan(engagement=engagement.pk))
        self.assertEqual(created["engagement_id"], engagement.pk)
        engagement.refresh_from_db()
        self.assertEqual(engagement.commit.sha, SHA)
        rejected = self.scan(engagement=engagement.pk, repository_url="https://github.com/example/other")
        self.assertEqual(rejected.status_code, 400, rejected.content[:1000])
        self.assert_repository_count(1)

    @override_settings(V3_FEATURE_LOCATIONS=True)
    def test_location_from_another_visible_product_is_rejected_before_writing_scm_context(self):
        self.hidden.authorized_users.add(self.member.pk)
        url = URL.objects.create(protocol="https", host="other-product.example.invalid")
        url.location.associate_with_product(self.hidden)
        response = self.scan(endpoint_to_add=url.location_id)
        self.assertEqual(response.status_code, 400, response.content[:1000])
        self.assert_repository_count(0)

    @override_settings(ASPM_SCM_HIERARCHY=False)
    def test_opt_in_field_is_rejected_when_disabled(self):
        self.assertEqual(self.scan().status_code, 400)
        self.assert_repository_count(0)

    def test_legacy_import_keeps_accepting_legacy_commit_values(self):
        day = timezone.localdate()
        engagement, = Engagement.objects.bulk_create([
            Engagement(product=self.product, name="Legacy import", target_start=day, target_end=day),
        ])
        created = self.assert_created(self.scan(legacy=True, engagement=engagement.pk, commit_hash="a1b2c3"))
        self.assertEqual(Test.objects.get(pk=created["test_id"]).commit_hash, "a1b2c3")
        self.assert_repository_count(0)


@override_settings(ASPM_SCM_HIERARCHY=True)
@skipUnlessDBFeature("has_select_for_update")
class TestConcurrentSCMScanContext(SimpleTestCase):
    # Committed fixtures are visible to both workers. Clean up our own rows rather
    # than flushing the schema, which contains retained Community compatibility FKs.
    databases = {"default"}

    @staticmethod
    def remove_user(user_id):
        get_user_model().objects.filter(pk=user_id).delete()
        apps.get_model("dojo", "Dojo_UserEvent").objects.filter(pgh_obj_id=user_id).delete()

    @staticmethod
    def remove_project(product_type_id):
        products = list(Product.objects.filter(prod_type_id=product_type_id).values_list("pk", flat=True))
        engagements = list(Engagement.objects.filter(product_id__in=products).values_list("pk", flat=True))
        with (
            patch("dojo.product.signals.create_notification"),
            patch("dojo.product_type.signals.create_notification"),
        ):
            Product_Type.objects.filter(pk=product_type_id).delete()
        for event, ids in (("Product_TypeEvent", [product_type_id]), ("ProductEvent", products), ("EngagementEvent", engagements)):
            apps.get_model("dojo", event).objects.filter(pgh_obj_id__in=ids).delete()

    def test_two_first_imports_resolve_the_same_engagement(self):
        user_model = get_user_model()
        suffix = uuid4().hex[:12]
        user = user_model.objects.create_superuser(username=f"aspm-scm-concurrent-{suffix}")
        self.addCleanup(self.remove_user, user.pk)
        product_type, = Product_Type.objects.bulk_create([Product_Type(name=f"Concurrent SCM type {suffix}")])
        self.addCleanup(self.remove_project, product_type.pk)
        product, = Product.objects.bulk_create([
            Product(name=f"Concurrent SCM product {suffix}", description="CI", prod_type=product_type),
        ])
        barrier = Barrier(2)
        payload = {"product_name": product.name, "repository_url": REPO_URL, "commit_hash": SHA}

        def first_import():
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET lock_timeout = '5s'")
                actor = user_model.objects.get(pk=user.pk)
                target = resolve_scm_scan(payload, AutoCreateContextManager(), actor, reimport=False)
                barrier.wait(timeout=5)
                engagement, _ = materialize_scm_scan(target, payload, actor, reimport=False)
                return engagement.pk
            finally:
                connections.close_all()

        with patch("dojo.engagement.signals.dojo_dispatch_task"), ThreadPoolExecutor(max_workers=2) as executor:
            first, second = (executor.submit(first_import) for _ in range(2))
            self.assertEqual(first.result(timeout=10), second.result(timeout=10))
        self.assertEqual(Repository.objects.filter(product=product).count(), 1)
        self.assertEqual(Commit.objects.filter(repository__product=product).count(), 1)
        self.assertEqual(Engagement.objects.filter(product=product).count(), 1)
