from importlib import import_module

from django.db import migrations, models

AddIndexConcurrentlyIfMissing = import_module("dojo.db_migrations.0305_archive_batch_indexes").AddIndexConcurrentlyIfMissing


def add_foreign_key(apps, schema_editor):
    schema_editor.execute("SET LOCAL lock_timeout = '3s'")
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM pg_constraint WHERE conrelid = 'dojo_engagement'::regclass AND conname = %s",
            ["aspm_engagement_commit_fk"],
        )
        if cursor.fetchone() is not None:
            return
    schema_editor.execute(
        "ALTER TABLE dojo_engagement ADD CONSTRAINT aspm_engagement_commit_fk "
        "FOREIGN KEY (commit_id) REFERENCES dojo_commit (id) DEFERRABLE INITIALLY DEFERRED NOT VALID",
    )


def validate_foreign_key(apps, schema_editor):
    schema_editor.execute("SET LOCAL lock_timeout = '3s'")
    schema_editor.execute("ALTER TABLE dojo_engagement VALIDATE CONSTRAINT aspm_engagement_commit_fk")


def remove_foreign_key(apps, schema_editor):
    schema_editor.execute("SET LOCAL lock_timeout = '3s'")
    schema_editor.execute("ALTER TABLE dojo_engagement DROP CONSTRAINT IF EXISTS aspm_engagement_commit_fk")


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("dojo", "0307_aspm_scm_hierarchy")]
    operations = [
        AddIndexConcurrentlyIfMissing(
            model_name="engagement",
            index=models.Index(fields=["commit", "id"], condition=models.Q(commit__isnull=False), name="aspm_engagement_commit_idx"),
        ),
        migrations.RunPython(add_foreign_key, remove_foreign_key, atomic=True),
        migrations.RunPython(validate_foreign_key, migrations.RunPython.noop, atomic=True),
        migrations.SeparateDatabaseAndState(state_operations=[
            migrations.AlterField(
                model_name="engagement", name="commit",
                field=models.ForeignKey(
                    "dojo.Commit", on_delete=models.SET_NULL, related_name="engagements",
                    null=True, blank=True, editable=False, db_index=False,
                ),
            ),
        ]),
    ]
