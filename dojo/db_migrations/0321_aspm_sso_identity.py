import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("dojo", "0320_aspm_engagement_policies")]

    operations = [
        migrations.CreateModel(
            name="SsoIdentity",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("issuer", models.URLField(max_length=500)),
                ("subject", models.CharField(max_length=255)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="aspm_sso_identity", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "constraints": [models.UniqueConstraint(fields=("issuer", "subject"), name="aspm_oidc_issuer_subject")],
            },
        ),
        migrations.CreateModel(
            name="SsoProductGrant",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("issuer", models.URLField(max_length=500)),
                ("group_id", models.UUIDField()),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="dojo.product")),
            ],
            options={
                "constraints": [models.UniqueConstraint(fields=("issuer", "group_id", "product"), name="aspm_oidc_product_grant")],
                "permissions": [("manage_sso_mapping", "Can manage ASPM SSO mappings")],
            },
        ),
    ]
