from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

BACKEND = "dojo.aspm_access.backend.KeycloakBackend"
USERNAME_PREFIX = "aspm-sso-"


def managed_account(user):
    return hasattr(user, "aspm_sso_identity")


class KeycloakBackend(BaseBackend):
    def get_user(self, user_id):
        return get_user_model().objects.filter(
            pk=user_id, is_active=True, is_staff=False, is_superuser=False,
            aspm_sso_identity__isnull=False,
        ).select_related("aspm_sso_identity").first()
