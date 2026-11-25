import hashlib
import json
import secrets
import uuid
from base64 import urlsafe_b64encode
from urllib.parse import urlencode, urlsplit

import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils.crypto import constant_time_compare

from dojo.aspm_access.backend import USERNAME_PREFIX
from dojo.aspm_access.models import SsoIdentity

MAX_DOCUMENT = 256 * 1024
STATE_AGE = 300


class InvalidLoginError(ValueError):
    pass


def options():
    issuer = settings.ASPM_OIDC_ISSUER
    callback = settings.ASPM_OIDC_CALLBACK_URL
    callback_url = urlsplit(callback)
    site = urlsplit(settings.SITE_URL)
    issuer_url = urlsplit(issuer)
    root = issuer_url.path.strip("/").split("/")
    if (
        not settings.ASPM_OIDC_CLIENT_ID or not settings.ASPM_OIDC_CLIENT_SECRET
        or issuer_url.scheme != "https" or not issuer_url.hostname or issuer_url.username is not None
        or issuer_url.query or issuer_url.fragment or issuer.endswith("/")
        or len(issuer) > 500 or len(root) < 2 or root[-2] != "realms" or not root[-1]
        or callback_url.scheme != "https" or callback_url.netloc != site.netloc or site.scheme != "https"
        or callback_url.path != reverse("aspm_oidc_callback") or callback_url.query or callback_url.fragment
        or callback_url.username is not None
        or "openid" not in settings.ASPM_OIDC_SCOPES or "offline_access" in settings.ASPM_OIDC_SCOPES
        or not 30 <= settings.ASPM_OIDC_GROUP_TTL <= min(600, settings.ASPM_OIDC_SESSION_AGE)
        or not 30 <= settings.ASPM_OIDC_SESSION_AGE <= 43200
        or not settings.SESSION_COOKIE_SECURE or not settings.CSRF_COOKIE_SECURE
        or settings.SESSION_COOKIE_SAMESITE != "Lax" or not settings.SESSION_COOKIE_HTTPONLY
        or settings.SESSION_ENGINE == "django.contrib.sessions.backends.signed_cookies"
        or settings.ASPM_OIDC_CLIENT_AUTH not in {"client_secret_basic", "client_secret_post"}
        or len({settings.ASPM_OIDC_SECOPS_ROLE, settings.ASPM_OIDC_EXPERT_ROLE, settings.ASPM_OIDC_USER_ROLE}) != 3
        or not all((settings.ASPM_OIDC_SECOPS_ROLE, settings.ASPM_OIDC_EXPERT_ROLE, settings.ASPM_OIDC_USER_ROLE))
        or settings.ASPM_OIDC_ROLE_CLAIM == settings.ASPM_OIDC_GROUP_CLAIM
        or not all((settings.ASPM_OIDC_ROLE_CLAIM, settings.ASPM_OIDC_GROUP_CLAIM))
    ):
        msg = "Invalid ASPM OIDC configuration. Check the HTTPS issuer, callback, client and session settings."
        raise ImproperlyConfigured(msg)
    return f"{issuer}/protocol/openid-connect", callback


def authorization_url(flow):
    endpoint, callback = options()
    challenge = urlsafe_b64encode(hashlib.sha256(flow["verifier"].encode()).digest()).rstrip(b"=").decode()
    query = urlencode({
        "client_id": settings.ASPM_OIDC_CLIENT_ID, "redirect_uri": callback, "response_type": "code",
        "scope": " ".join(settings.ASPM_OIDC_SCOPES), "state": flow["state"], "nonce": flow["nonce"],
        "code_challenge": challenge, "code_challenge_method": "S256",
    })
    return f"{endpoint}/auth?{query}"


def _json_response(method, url, **kwargs):
    with requests.Session() as session:
        # The identity provider and CA are configured by the operator.
        session.trust_env = False
        with session.request(
            method, url, allow_redirects=False, stream=True, timeout=(3, 5),
            verify=settings.ASPM_OIDC_CA_BUNDLE or True, **kwargs,
        ) as response:
            if response.status_code != 200:
                raise InvalidLoginError
            content = bytearray()
            for chunk in response.iter_content(16384):
                content.extend(chunk)
                if len(content) > MAX_DOCUMENT:
                    raise InvalidLoginError
            document = json.loads(content)
            if not isinstance(document, dict):
                raise InvalidLoginError
            return document


def exchange_code(code, flow):
    endpoint, callback = options()
    fields = {"grant_type": "authorization_code", "code": code, "redirect_uri": callback, "code_verifier": flow["verifier"]}
    credentials = (settings.ASPM_OIDC_CLIENT_ID, settings.ASPM_OIDC_CLIENT_SECRET)
    if settings.ASPM_OIDC_CLIENT_AUTH == "client_secret_post":
        fields["client_id"], fields["client_secret"] = credentials
        credentials = None
    token = _json_response("POST", f"{endpoint}/token", data=fields, auth=credentials).get("id_token")
    if not isinstance(token, str) or len(token) > 32768:
        raise InvalidLoginError
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if header.get("alg") != "RS256" or not isinstance(kid, str) or not kid:
        raise InvalidLoginError
    keys = _json_response("GET", f"{endpoint}/certs").get("keys")
    if not isinstance(keys, list):
        raise InvalidLoginError
    matches = [
        key for key in keys if isinstance(key, dict) and key.get("kid") == kid
        and key.get("kty") == "RSA" and key.get("use", "sig") == "sig" and key.get("alg", "RS256") == "RS256"
    ]
    if len(matches) != 1:
        raise InvalidLoginError
    key = jwt.PyJWK.from_dict(matches[0], algorithm="RS256").key
    if key.key_size < 2048:
        raise InvalidLoginError
    claims = jwt.decode(
        token, key, algorithms=["RS256"], audience=settings.ASPM_OIDC_CLIENT_ID,
        issuer=settings.ASPM_OIDC_ISSUER, options={"require": ["iss", "sub", "aud", "iat", "exp", "nonce"]},
    )
    subject = claims["sub"]
    authorized_party = claims.get("azp")
    audience = claims["aud"]
    if (
        not isinstance(subject, str) or not 0 < len(subject) <= 255 or any(ord(char) < 32 for char in subject)
        or not isinstance(claims["nonce"], str) or not constant_time_compare(claims["nonce"], flow["nonce"])
        or (isinstance(audience, list) and len(audience) > 1 and authorized_party is None)
        or (authorized_party is not None and authorized_party != settings.ASPM_OIDC_CLIENT_ID)
    ):
        raise InvalidLoginError
    return claims


def _values(claims, name):
    value = claims.get(name, [])
    if not isinstance(value, list) or len(value) > 256 or any(not isinstance(entry, str) or len(entry) > 255 for entry in value):
        raise InvalidLoginError
    return value


def session_claims(claims):
    roles = _values(claims, settings.ASPM_OIDC_ROLE_CLAIM)
    groups = []
    if settings.ASPM_OIDC_SECOPS_ROLE in roles:
        role = "secops"
    elif settings.ASPM_OIDC_EXPERT_ROLE in roles:
        role = "expert"
    else:
        role = "user"
        if settings.ASPM_OIDC_USER_ROLE in roles:
            groups = sorted({str(uuid.UUID(entry)) for entry in _values(claims, settings.ASPM_OIDC_GROUP_CLAIM)})
    return role, groups


def resolve_identity(issuer, subject):
    existing = SsoIdentity.objects.select_related("user").filter(issuer=issuer, subject=subject).first()
    if existing:
        return existing
    try:
        with transaction.atomic():
            user = get_user_model().objects.create_user(username=USERNAME_PREFIX + secrets.token_hex(18))
            return SsoIdentity.objects.create(issuer=issuer, subject=subject, user=user)
    except IntegrityError:
        # Two valid callbacks for the same subject can finish simultaneously.
        return SsoIdentity.objects.select_related("user").get(issuer=issuer, subject=subject)
