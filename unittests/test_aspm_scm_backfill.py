from datetime import date
from importlib import import_module
from unittest.mock import patch

from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase

SCHEMA = ("dojo", "0308_aspm_scm_engagement_constraints")
BACKFILL = ("dojo", "0309_aspm_scm_backfill")
REPOSITORY_URL = "https://github.com/org/repo"
SHA = "abcdef0123456789abcd" * 2
SHA256 = "abcdef0123456789" * 4
LEGACY_URL = "https://GitHub.com:443/org/repo.git/"


class SCMBackfillTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.schema_state = MigrationLoader(connection).project_state(SCHEMA)
        cls.migration = import_module(f"dojo.db_migrations.{BACKFILL[1]}")
        apps = cls.schema_state.apps
        cls.engagement_model = apps.get_model("dojo", "Engagement")
        cls.repository_model = apps.get_model("dojo", "Repository")
        cls.commit_model = apps.get_model("dojo", "Commit")
        product_type = apps.get_model("dojo", "Product_Type").objects.create(name="SCM migration products")
        products = apps.get_model("dojo", "Product").objects
        product = products.create(name="SCM backfill product", prod_type_id=product_type.pk)
        other_product = products.create(name="Other SCM backfill product", prod_type_id=product_type.pk)

        repo = cls.repository_model.objects.create(product_id=product.pk, url=REPOSITORY_URL, provider="github")
        cls.existing_commit_id = cls.commit_model.objects.create(repository_id=repo.pk, sha=SHA, branch="manual").pk
        cls.existing_link_id = cls.engagement(product.pk, "https://example.com/other/project", SHA256, cls.existing_commit_id)
        cls.valid_id = cls.engagement(product.pk, LEGACY_URL, SHA.upper())
        cls.invalid_sha_id = cls.engagement(product.pk, REPOSITORY_URL, "0123")
        cls.same_commit_id = cls.engagement(product.pk, REPOSITORY_URL, SHA)
        cls.unsafe_uri_id = cls.engagement(product.pk, "https://user:pass@github.com/org/repo", SHA)
        cls.other_product_id = cls.engagement(other_product.pk, REPOSITORY_URL, SHA)
        cls.sha256_id = cls.engagement(product.pk, REPOSITORY_URL, SHA256.upper())

    @classmethod
    def engagement(cls, product_id, uri, sha, commit_id=None):
        return cls.engagement_model.objects.create(
            product_id=product_id,
            target_start=date(2026, 1, 1),
            target_end=date(2026, 1, 2),
            source_code_management_uri=uri,
            commit_hash=sha,
            branch_tag="legacy",
            commit_id=commit_id,
        ).pk

    def run_backfill(self, *, reverse=False):
        migration, state = type(self).migration, type(self).schema_state
        operation, = migration.Migration.operations
        run = operation.database_backwards if reverse else operation.database_forwards
        with connection.schema_editor(atomic=False) as schema_editor, patch.object(migration, "BATCH_SIZE", 2):
            run("dojo", schema_editor, state, state)

    def test_links_valid_legacy_values_in_chunks_and_preserves_existing_data(self):
        self.run_backfill()

        engagements = self.engagement_model.objects.in_bulk()
        valid = engagements[self.valid_id]
        same_commit = engagements[self.same_commit_id]
        other_product = engagements[self.other_product_id]
        sha256 = engagements[self.sha256_id]
        existing_link = engagements[self.existing_link_id]

        self.assertEqual(valid.commit_id, self.existing_commit_id)
        self.assertEqual(same_commit.commit_id, valid.commit_id)
        self.assertEqual(existing_link.commit_id, self.existing_commit_id)
        self.assertEqual(valid.commit.branch, "manual")
        self.assertEqual(valid.source_code_management_uri, LEGACY_URL)
        self.assertEqual(valid.commit_hash, SHA.upper())
        self.assertEqual(valid.branch_tag, "legacy")
        self.assertEqual(other_product.commit.repository.product_id, other_product.product_id)
        self.assertEqual(other_product.commit.repository.provider, "github")
        self.assertNotEqual(other_product.commit_id, valid.commit_id)
        self.assertEqual(sha256.commit.sha, SHA256)
        self.assertEqual(sha256.commit.branch, "")
        self.assertIsNone(engagements[self.invalid_sha_id].commit_id)
        self.assertIsNone(engagements[self.unsafe_uri_id].commit_id)
        repos = self.repository_model.objects.filter(product_id__in=(valid.product_id, other_product.product_id))
        commits = self.commit_model.objects.filter(repository__in=repos)
        self.assertEqual(repos.count(), 2)
        self.assertEqual(commits.count(), 3)

        self.run_backfill(reverse=True)
        self.run_backfill()

        valid.refresh_from_db()
        existing_link.refresh_from_db()
        self.assertEqual(valid.commit_id, self.existing_commit_id)
        self.assertEqual(existing_link.commit_id, self.existing_commit_id)
        self.assertEqual(repos.count(), 2)
        self.assertEqual(commits.count(), 3)
