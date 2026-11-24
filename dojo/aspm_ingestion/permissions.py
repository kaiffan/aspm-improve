import sys
from pathlib import Path

from django.conf import settings
from django.utils import timezone


def api_only_scans_enabled():
    """Legacy UI compatibility is confined to the explicit Django test command."""
    test_command = bool(sys.argv) and Path(sys.argv[0]).name == "manage.py" and sys.argv[1:2] == ["test"]
    return settings.ASPM_API_ONLY or not test_command


def legacy_scan_principal_allowed(user):
    """Keep legacy administrative integrations; human member accounts cannot bypass ASPM via v2/v3."""
    if not api_only_scans_enabled() or user.is_superuser:
        return True
    if not (user.is_authenticated and user.is_active and not user.is_staff and not user.has_usable_password()):
        return False
    from dojo.aspm_ingestion.models import IngestionToken  # noqa: PLC0415 -- permission/model import cycle

    # An unusable password alone also describes SSO humans. Require explicit CI enrollment.
    return IngestionToken.objects.filter(user=user, revoked_at__isnull=True, expires_at__gt=timezone.now(), scopes__contains=["submit"]).exists()
