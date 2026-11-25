from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("dojo", "0318_aspm_transactional_webhook_events")]
    operations = [migrations.AddField(model_name="webhookdelivery", name="dispatch_until", field=models.DateTimeField(blank=True, null=True))]
