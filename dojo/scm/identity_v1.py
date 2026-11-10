"""Stable SCM identity rules shared with the initial data migration."""

import re
from ipaddress import IPv6Address
from urllib.parse import urlsplit, urlunsplit

HOST_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*")
SHA_PATTERN = re.compile(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})")
PROVIDERS = {
    "github.com": "github",
    "gitlab.com": "gitlab",
    "bitbucket.org": "bitbucket",
    "dev.azure.com": "azure",
}


def canonical_repository_url(value):
    msg = "Invalid SCM repository URL."
    if not isinstance(value, str) or any(character.isspace() or ord(character) < 32 for character in value):
        raise ValueError(msg)
    if "?" in value or "#" in value or "\\" in value:
        raise ValueError(msg)
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username is not None:
        raise ValueError(msg)
    if ":" in parts.hostname:
        host = f"[{IPv6Address(parts.hostname)}]"
    else:
        host = parts.hostname.rstrip(".").encode("idna").decode("ascii").lower()
        if not HOST_PATTERN.fullmatch(host):
            raise ValueError(msg)
    port = parts.port
    if port is not None and port != {"http": 80, "https": 443}[parts.scheme]:
        host = f"{host}:{port}"
    path = parts.path.rstrip("/")
    if path.endswith(".git.git") or any(segment in {".", "..", ".git"} for segment in path.split("/")):
        raise ValueError(msg)
    path = path.removesuffix(".git")
    result = urlunsplit((parts.scheme, host, path, "", ""))
    if not path.strip("/") or len(result) > 600:
        raise ValueError(msg)
    return result


def canonical_sha(value):
    if not isinstance(value, str) or not SHA_PATTERN.fullmatch(value):
        msg = "Invalid full Git commit SHA."
        raise ValueError(msg)
    return value.lower()


def repository_provider(url):
    host = urlsplit(url).hostname
    if host and host.endswith(".visualstudio.com"):
        return "azure"
    return PROVIDERS.get(host, "other")
