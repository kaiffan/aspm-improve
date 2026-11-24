import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("dojo", "0312_aspm_evidence_guards")]
    operations = [migrations.SeparateDatabaseAndState(state_operations=[migrations.CreateModel(
        name="IngestionRateWindow",
        fields=[("token", models.OneToOneField(primary_key=True, serialize=False, on_delete=django.db.models.deletion.CASCADE, to="dojo.ingestiontoken")),
                ("bucket_minute", models.BigIntegerField()), ("requests", models.IntegerField())],
        options={"db_table": "aspm_ingestion_rate"},
    )])]
