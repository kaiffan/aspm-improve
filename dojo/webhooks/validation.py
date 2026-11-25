import ipaddress
import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError

from dojo.webhooks.catalog import EVENT_TYPES, FILTER_FIELDS


def public_address(value):
    address = ipaddress.ip_address(value)
    if not address.is_global or address.is_multicast or address.is_reserved:
        return False
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped:
            return public_address(str(address.ipv4_mapped))
        if address.sixtofour or address.teredo or address in ipaddress.IPv6Network("64:ff9b::/96") or address in ipaddress.IPv6Network("64:ff9b:1::/48"):
            return False
    return True


def validate_endpoint(value):
    try:
        url = urlsplit(value)
        if url.scheme != "https" or not url.hostname or url.username or url.password or url.fragment or url.query or url.port not in {None, 443}:
            raise ValueError
        host = url.hostname.encode("idna").decode("ascii")
        if not re.fullmatch(r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", host, re.IGNORECASE) or any(c in value for c in "\r\n\\"):
            raise ValueError
        try:
            if not public_address(host):
                raise ValueError
        except ValueError as error:
            # A numeric address must pass the same global-unicast policy as DNS answers.
            if host.replace(".", "").isdigit() or ":" in host:
                raise ValueError from error
    except (ValueError, UnicodeError) as error:
        msg = "Use a public HTTPS endpoint on port 443, without credentials, query or fragment."
        raise ValidationError(msg) from error
    return value


def validate_rules(events, filters):
    if not isinstance(events, list) or not events or len(events) > len(EVENT_TYPES) or not all(isinstance(e, str) and e in EVENT_TYPES for e in events):
        msg = "Select known event types from the version 1 catalogue."
        raise ValidationError(msg)
    if not isinstance(filters, dict) or not set(filters) <= FILTER_FIELDS:
        msg = "Unknown webhook filter field."
        raise ValidationError(msg)
    for key, values in filters.items():
        if not isinstance(values, list) or not 1 <= len(values) <= 50 or not all(isinstance(v, str) and 0 < len(v) <= 200 for v in values):
            msg = "Each filter must contain 1-50 nonempty strings, each at most 200 characters."
            raise ValidationError(msg)
        if key == "repository_id" and not all(v.isdecimal() and 0 < int(v) <= 2**63 - 1 for v in values):
            msg = "Repository filters use positive decimal IDs."
            raise ValidationError(msg)
        if key == "severity" and not set(values) <= {"Critical", "High", "Medium", "Low", "Info"}:
            msg = "Unknown severity."
            raise ValidationError(msg)
        if key == "finding_status" and not set(values) <= {"active", "mitigated", "false_positive", "duplicate", "out_of_scope", "inactive"}:
            msg = "Unknown finding status."
            raise ValidationError(msg)


def matches(filters, payload):
    attributes = payload.get("attributes", {})
    for field, allowed in filters.items():
        actual = attributes.get(field)
        actual = actual if isinstance(actual, list) else [actual]
        if not {str(v) for v in actual if v is not None} & set(allowed):
            return False
    return True
