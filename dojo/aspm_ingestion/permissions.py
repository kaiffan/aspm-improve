from django.conf import settings


def legacy_scan_principal_allowed(user):
    """Keep legacy administrative integrations; human member accounts cannot bypass ASPM via v2/v3."""
    return not settings.ASPM_API_ONLY or user.is_superuser or (
        user.is_authenticated and user.is_active and not user.is_staff and not user.has_usable_password()
    )
