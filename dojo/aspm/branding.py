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


def _color(value):
    if value and not re.fullmatch(r"#[a-fA-F0-9]{6}", value):
        msg = "ASPM branding colors must use six-digit HEX values."
        raise ImproperlyConfigured(msg)
    return value


def _text_color(hex_color):
    channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    luminance = sum(coefficient * channel for coefficient, channel in zip((0.2126, 0.7152, 0.0722), linear, strict=True))
    return "#000000" if luminance > 0.179 else "#ffffff"


def get_branding():
    """Return public presentation metadata without database or network access."""
    revision = getattr(settings, "ASPM_GIT_SHA", "")
    primary = _color(getattr(settings, "ASPM_BRAND_PRIMARY", ""))
    return {
        **_RELEASE,
        "primary": primary,
        "on_primary": _text_color(primary) if primary else "",
        "secondary": _color(getattr(settings, "ASPM_BRAND_SECONDARY", "")),
        "accent": _color(getattr(settings, "ASPM_BRAND_ACCENT", "")),
        "build_timestamp": getattr(settings, "ASPM_BUILD_TIMESTAMP", ""),
        "name": getattr(settings, "ASPM_BRAND_NAME", "ASPM").strip() or "ASPM",
        "mark": _asset(getattr(settings, "ASPM_BRAND_MARK", "dojo/img/aspm-mark.svg")),
        "favicon": _asset(getattr(settings, "ASPM_FAVICON", "dojo/img/aspm-mark.svg")),
        "git_sha": revision if re.fullmatch(r"[a-f0-9]{40,64}", revision) else "development",
        "git_short_sha": revision[:12] if re.fullmatch(r"[a-f0-9]{40,64}", revision) else "development",
    }
