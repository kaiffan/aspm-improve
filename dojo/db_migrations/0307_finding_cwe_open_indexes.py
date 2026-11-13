from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("dojo", "0306_system_settings_read_only_mode"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="finding",
            index=models.Index(fields=["test", "cwe"], include=["id"], name="idx_finding_test_cwe_cover"),
        ),
        AddIndexConcurrently(
            model_name="finding",
            index=models.Index(
                fields=["test"],
                condition=models.Q(active=True, false_p=False, duplicate=False, out_of_scope=False, mitigated__isnull=True),
                name="idx_finding_open_test",
            ),
        ),
    ]
