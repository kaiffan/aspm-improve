from django.conf import settings
from django.db import models


class SsoIdentity(models.Model):
    issuer = models.URLField(max_length=500)
    subject = models.CharField(max_length=255)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="aspm_sso_identity")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("issuer", "subject"), name="aspm_oidc_issuer_subject")]


class SsoProductGrant(models.Model):
    issuer = models.URLField(max_length=500)
    group_id = models.UUIDField()
    product = models.ForeignKey("dojo.Product", on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("issuer", "group_id", "product"), name="aspm_oidc_product_grant")]
        permissions = [("manage_sso_mapping", "Can manage ASPM SSO mappings")]
