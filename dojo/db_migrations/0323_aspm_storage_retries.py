# ruff: noqa: N999 -- Django migration filename
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("dojo", "0322_aspm_stored_objects")]

    operations = [
        migrations.AddField(model_name="ingestionjob", name="storage_failures", field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name="ingestionjob", name="storage_retry_at", field=models.DateTimeField(blank=True, null=True)),
    ]
