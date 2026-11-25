from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, close_old_connections, connections, transaction
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from dojo.aspm_ingestion.models import EngagementPolicy, ManagedEngagement, ScanRun
from dojo.engagement.models import Engagement
from dojo.scm.models import Repository
from unittests import test_aspm_ingestion
from unittests.test_aspm_ingestion import SHA, URL, IngestionFixture, generic


class EngagementPolicyTests(IngestionFixture, APITestCase):
    def setUp(self):
        self.setup_ingestion()

    def test_default_keeps_one_commit_engagement_per_run(self):
        first = self.complete(self.accepted(key="default-1"))
        second = self.complete(self.accepted(key="default-2"))
        self.assertIsNone(first.engagement_id)
        self.assertEqual(first.test.engagement.commit_id, first.commit_id)
        self.assertNotEqual(first.test.engagement_id, second.test.engagement_id)

    def test_repository_policy_reuses_engagement_but_preserves_tests_and_observations(self):
        policy = EngagementPolicy.objects.create(product=self.product, strategy="repository")
        first = self.complete(self.accepted(key="first"))
        second = self.complete(self.accepted(key="second", commit_sha="b" * 40))
        self.assertEqual(first.engagement_id, second.engagement_id)
        self.assertEqual(first.test.engagement_id, first.engagement_id)
        self.assertEqual(second.test.engagement_id, second.engagement_id)
        self.assertNotEqual(first.test_id, second.test_id)
        self.assertEqual((first.observations.count(), second.observations.count()), (1, 1))
        policy.strategy = "explicit"
        policy.save(update_fields=["strategy"])
        replay = self.upload(key="first")
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json()["id"], str(first.pk))

    def test_override_branch_environment_and_archive(self):
        EngagementPolicy.objects.create(product=self.product, strategy="branch")
        self.assertEqual(self.upload().status_code, 400)
        main = self.accepted(key="main", branch="main")
        feature = self.accepted(key="feature", branch="feature")
        self.assertNotEqual(main.engagement_id, feature.engagement_id)
        EngagementPolicy.objects.create(product=self.product, repository=main.commit.repository, strategy="environment")
        self.assertEqual(self.upload(key="missing-env", branch="main").status_code, 400)
        prod = self.accepted(key="prod", environment="prod")
        staging = self.accepted(key="staging", environment="staging")
        self.assertNotEqual(prod.engagement_id, staging.engagement_id)
        ManagedEngagement.objects.filter(engagement_id=prod.engagement_id).update(archived_at=timezone.now())
        successor = self.accepted(key="prod2", environment="prod")
        self.assertNotEqual(prod.engagement_id, successor.engagement_id)
        self.assertEqual(self.complete(prod).test.engagement_id, prod.engagement_id)

    def test_environment_is_an_independent_evidence_slot(self):
        from dojo.aspm_ingestion.selection import live_selection  # noqa: PLC0415 -- evidence integration

        first = self.complete(self.accepted(key="prod", pipeline_id="ci", scan_scope="source", environment="production"))
        second = self.complete(self.accepted(key="dev", pipeline_id="ci", scan_scope="source", environment="development"))
        selected = live_selection(first.commit)
        self.assertEqual(set(selected["completed_ids"]), {first.pk, second.pk})
        self.assertFalse(selected["ambiguous"])

    @override_settings(ASPM_DEFAULT_ENGAGEMENT_POLICY="explicit")
    def test_explicit_scope_and_db_guards(self):
        def make_engagement(product):
            today = timezone.localdate()
            return Engagement.objects.create(product=product, name="Explicit", target_start=today, target_end=today)

        allowed = make_engagement(self.product)
        hidden = make_engagement(self.hidden)
        self.assertEqual(self.upload().status_code, 400)
        self.assertEqual(self.upload(engagement_id=allowed.pk).status_code, 403)
        self.token.scopes.append("engagement:select")
        self.token.save(update_fields=["scopes"])
        self.assertEqual(self.upload(engagement_id=hidden.pk).status_code, 403)
        accepted = self.accepted(engagement_id=allowed.pk)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Engagement.objects.filter(pk=allowed.pk).update(product=self.hidden)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ScanRun.objects.filter(pk=accepted.pk).update(engagement=hidden)
        self.assertEqual(self.complete(accepted).test.engagement_id, allowed.pk)

    def test_repository_identity_uses_product_and_url(self):
        EngagementPolicy.objects.create(product=self.product, strategy="repository")
        first = self.accepted(key="repo-first")
        second = self.accepted(key="repo-second", repository_url="https://git.example.com/another/application")
        self.assertNotEqual(first.engagement_id, second.engagement_id)
        self.assertNotEqual(first.commit.repository_id, second.commit.repository_id)


class ConcurrentEngagementPolicyTests(test_aspm_ingestion.AspmConcurrentDeliveryTests):
    def tearDown(self):
        ScanRun.objects.filter(product=self.product).delete()
        engagements = list(ManagedEngagement.objects.filter(repository__product=self.product).values_list("engagement_id", flat=True))
        ManagedEngagement.objects.filter(repository__product=self.product).delete()
        Engagement.objects.filter(pk__in=engagements).delete()
        super().tearDown()

    def test_ten_jobs_create_one_repository_binding_across_commits(self):
        repository = Repository.objects.create(product=self.product, url=URL)
        EngagementPolicy.objects.create(product=self.product, strategy="repository")
        barrier = Barrier(10)

        def post(index):
            close_old_connections()
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f"ASPM {self.raw}")
            try:
                barrier.wait(timeout=10)
                response = client.post(reverse("aspm_v1:scans"), {
                    "project_id": self.product.pk, "repository_id": repository.pk,
                    "commit_sha": SHA if index % 2 else "b" * 40,
                    "scanner_type": "Generic Findings Import", "idempotency_key": f"job-{index}",
                    "file": SimpleUploadedFile("scan.json", generic()),
                }, format="multipart")
                return response.status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=10) as pool:
            self.assertEqual(list(pool.map(post, range(10))), [202] * 10)
        scans = ScanRun.objects.filter(product=self.product)
        self.assertEqual(scans.count(), 10)
        binding = ManagedEngagement.objects.get(repository=repository)
        self.assertEqual(set(scans.values_list("engagement_id", flat=True)), {binding.engagement_id})
