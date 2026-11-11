"""Replaceable local branding, independent from permissions and upstream version."""
import json
import re
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_RELEASE = json.loads(Path(__file__).with_name("release.json").read_text())


def _asset(value):
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", value) or PurePosixPath(value).is_absolute() or ".." in PurePosixPath(value).parts:
        msg = "ASPM branding assets must be relative local static paths."
        raise ImproperlyConfigured(msg)
    return value


def get_branding():
    """Return public presentation metadata without database or network access."""
    revision = getattr(settings, "ASPM_GIT_SHA", "")
    return {
        **_RELEASE,
        "name": getattr(settings, "ASPM_BRAND_NAME", "ASPM").strip() or "ASPM",
        "mark": _asset(getattr(settings, "ASPM_BRAND_MARK", "dojo/img/aspm-mark.svg")),
        "favicon": _asset(getattr(settings, "ASPM_FAVICON", "dojo/img/aspm-mark.svg")),
        "git_sha": revision if re.fullmatch(r"[a-f0-9]{40,64}", revision) else "development",
        "git_short_sha": revision[:12] if re.fullmatch(r"[a-f0-9]{40,64}", revision) else "development",
    }
