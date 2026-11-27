# ruff: noqa: N999 -- Django migration filename
import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("dojo", "0321_aspm_sso_identity")]

    operations = [
        migrations.CreateModel(
            name="StoredObject",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=400, unique=True)),
                ("backend", models.CharField(default="s3", max_length=20)),
                ("bucket", models.CharField(max_length=255)),
                ("object_key", models.CharField(max_length=500)),
                ("version_id", models.CharField(blank=True, max_length=1024)),
                ("sha256", models.CharField(max_length=64)),
                ("size", models.PositiveBigIntegerField()),
                ("content_type", models.CharField(max_length=255)),
                ("state", models.CharField(choices=[("staged", "Staged"), ("ready", "Ready"), ("retired", "Retired")], default="staged", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"indexes": [models.Index(fields=["state", "updated_at"], name="aspm_object_state_age")]},
        ),
    ]
