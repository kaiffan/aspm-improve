import django.db.models.deletion
from django.db import migrations, models


SCAN_GUARD = r"""CREATE OR REPLACE FUNCTION aspm_guard_scan() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM dojo_commit c JOIN dojo_repository r ON r.id=c.repository_id
                   WHERE c.id=NEW.commit_id AND r.product_id=NEW.product_id) THEN
        RAISE EXCEPTION 'ASPM scan product/commit mismatch' USING ERRCODE='23514';
    END IF;
    {assignment}
    IF NEW.test_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM dojo_test t JOIN dojo_engagement e ON e.id=t.engagement_id
        WHERE t.id=NEW.test_id AND e.product_id=NEW.product_id {test_scope}
    ) THEN
        RAISE EXCEPTION 'ASPM scan test mismatch' USING ERRCODE='23514';
    END IF;
    IF TG_OP='UPDATE' THEN
        IF OLD.status='COMPLETED' OR
           ROW(NEW.product_id,NEW.commit_id,NEW.submitted_by_id,NEW.delivery_key,NEW.fingerprint,
               NEW.scanner,NEW.metadata,NEW.artifact_path,NEW.artifact_sha256,NEW.artifact_size,NEW.original_name)
           IS DISTINCT FROM
           ROW(OLD.product_id,OLD.commit_id,OLD.submitted_by_id,OLD.delivery_key,OLD.fingerprint,
               OLD.scanner,OLD.metadata,OLD.artifact_path,OLD.artifact_sha256,OLD.artifact_size,OLD.original_name)
           {immutable_assignment}
           OR (OLD.test_id IS NOT NULL AND NEW.test_id IS DISTINCT FROM OLD.test_id) THEN
            RAISE EXCEPTION 'ASPM evidence identity is immutable' USING ERRCODE='23514';
        END IF;
    END IF;
    RETURN NEW;
END $$;"""

ASSIGNMENT = r"""
    IF NEW.engagement_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM dojo_engagement e WHERE e.id=NEW.engagement_id
        AND e.product_id=NEW.product_id AND (e.commit_id IS NULL OR e.commit_id=NEW.commit_id)
        FOR SHARE
    ) THEN
        RAISE EXCEPTION 'ASPM assigned engagement mismatch' USING ERRCODE='23514';
    END IF;
"""

ENGAGEMENT_SCOPE = r"""
    IF EXISTS (SELECT 1 FROM dojo_scanrun WHERE engagement_id=OLD.id) THEN
        RAISE EXCEPTION 'ASPM assigned engagement identity is immutable' USING ERRCODE='23514';
    END IF;
"""

SOURCE_GUARD = r"""
CREATE OR REPLACE FUNCTION aspm_guard_engagement_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    {assignment}
    IF EXISTS (SELECT 1 FROM dojo_scanrun s JOIN dojo_test t ON t.id=s.test_id WHERE t.engagement_id=OLD.id) THEN
        RAISE EXCEPTION 'ASPM source engagement identity is immutable' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
"""

FORWARD = SCAN_GUARD.format(
    assignment=ASSIGNMENT,
    test_scope="""AND (
        (NEW.engagement_id IS NULL AND e.commit_id=NEW.commit_id) OR t.engagement_id=NEW.engagement_id
    )""",
    immutable_assignment="OR NEW.engagement_id IS DISTINCT FROM OLD.engagement_id",
) + SOURCE_GUARD.format(assignment=ENGAGEMENT_SCOPE)

REVERSE = r"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM dojo_scanrun WHERE engagement_id IS NOT NULL) THEN
        RAISE EXCEPTION 'ASPM engagement schema rollback requires a pre-policy data snapshot';
    END IF;
END $$;
""" + SCAN_GUARD.format(
    assignment="", test_scope="AND e.commit_id=NEW.commit_id", immutable_assignment="",
) + SOURCE_GUARD.format(assignment="")


class Migration(migrations.Migration):
    dependencies = [("dojo", "0319_aspm_webhook_dispatch_lease")]

    operations = [
        migrations.AddField(
            model_name="scanrun",
            name="engagement",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="dojo.engagement"),
        ),
        migrations.CreateModel(
            name="EngagementPolicy",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("strategy", models.CharField(
                    choices=[("default", "Default"), ("repository", "Repository"), ("branch", "Branch"),
                             ("environment", "Environment"), ("explicit", "Explicit")],
                    default="default", max_length=16,
                )),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="dojo.product")),
                ("repository", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="dojo.repository")),
            ],
            options={
                "permissions": [("manage_engagement_policy", "Can manage ASPM engagement policies")],
                "constraints": [
                    models.UniqueConstraint(condition=models.Q(repository__isnull=True), fields=("product",), name="aspm_product_engagement_policy"),
                    models.UniqueConstraint(condition=models.Q(repository__isnull=False), fields=("repository",), name="aspm_repo_engagement_policy"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ManagedEngagement",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("strategy", models.CharField(
                    choices=[("default", "Default"), ("repository", "Repository"), ("branch", "Branch"),
                             ("environment", "Environment"), ("explicit", "Explicit")],
                    max_length=16,
                )),
                ("scope", models.CharField(blank=True, max_length=150)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
                ("engagement", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to="dojo.engagement")),
                ("repository", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="dojo.repository")),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(archived_at__isnull=True), fields=("repository", "strategy", "scope"),
                        name="aspm_active_engagement_scope",
                    ),
                ],
            },
        ),
        migrations.RunSQL(FORWARD, REVERSE),
    ]
