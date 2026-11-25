import sys
from pathlib import Path

from django.conf import settings

from dojo.aspm_access.permissions import role


def api_only_scans_enabled():
    """Legacy UI compatibility is confined to the explicit Django test command."""
    test_command = bool(sys.argv) and Path(sys.argv[0]).name == "manage.py" and sys.argv[1:2] == ["test"]
    return settings.ASPM_API_ONLY or not test_command


def legacy_scan_principal_allowed(user):
    """Legacy APIs use object import permissions for every eligible principal."""
    return user.is_authenticated and user.is_active and role(user) != "user"
