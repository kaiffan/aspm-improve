import secrets
import time
from urllib.parse import urlencode

import jwt
import requests
from django.conf import settings
from django.contrib.auth import login, logout
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from dojo.aspm_observability import metrics as telemetry
from dojo.aspm_access.backend import BACKEND
from dojo.aspm_access.middleware import FLOW_KEY, SESSION_KEY
from dojo.aspm_access.oidc import (
    STATE_AGE,
    authorization_url,
    exchange_code,
    options,
    resolve_identity,
    session_claims,
)


@never_cache
@require_GET
def start(request):
    if not settings.ASPM_OIDC_ENABLED:
        raise Http404
    destination = request.GET.get("next", "")
    if not destination.startswith("/") or not url_has_allowed_host_and_scheme(destination, allowed_hosts=set(), require_https=True):
        destination = ""
    flow = {
        "state": secrets.token_urlsafe(32), "nonce": secrets.token_urlsafe(32), "verifier": secrets.token_urlsafe(48),
        "destination": destination, "started": time.time(),
    }
    url = authorization_url(flow)
    request.session[FLOW_KEY] = flow
    response = redirect(url)
    response["Referrer-Policy"] = "no-referrer"
    return response


@never_cache
@require_GET
def callback(request):
    if not settings.ASPM_OIDC_ENABLED:
        raise Http404
    flow = request.session.pop(FLOW_KEY, None)
    code = request.GET.get("code", "")
    state = request.GET.get("state", "")
    if (
        not flow or len(request.GET.getlist("state")) != 1 or len(request.GET.getlist("code")) != 1
        or not 0 < len(code) <= 4096 or len(state) != len(flow["state"]) or request.GET.get("error")
        or not constant_time_compare(state, flow["state"]) or time.time() - flow["started"] > STATE_AGE
        or request.GET.get("iss", settings.ASPM_OIDC_ISSUER) != settings.ASPM_OIDC_ISSUER
    ):
        return HttpResponseBadRequest("The sign-in request expired or was declined. Start sign-in again.")
    try:
        claims = exchange_code(code, flow)
        role, groups = session_claims(claims)
        expires = min(int(claims["exp"]), int(time.time()) + settings.ASPM_OIDC_SESSION_AGE)
    except (ValueError, TypeError, jwt.PyJWTError, requests.RequestException) as error:
        if telemetry.ENABLED and isinstance(error, requests.RequestException):
            telemetry.IDENTITY.labels("provider", "unavailable").inc()
        return HttpResponseBadRequest("The identity provider could not complete sign-in. Start sign-in again.")
    identity = resolve_identity(settings.ASPM_OIDC_ISSUER, claims["sub"])
    user = identity.user
    if not user.is_active or user.is_staff or user.is_superuser or user.has_usable_password():
        return HttpResponseForbidden()
    request.session.cycle_key()
    login(request, user, backend=BACKEND)
    request.session.set_expiry(settings.ASPM_OIDC_SESSION_AGE)
    request.session[SESSION_KEY] = {
        "role": role, "groups": groups, "issuer": identity.issuer, "expires": expires, "checked": int(time.time()),
    }
    response = redirect(flow["destination"] or reverse("aspm_projects"))
    response["Referrer-Policy"] = "no-referrer"
    return response


@never_cache
@require_POST
def end(request):
    destination = settings.LOGIN_URL
    if settings.ASPM_OIDC_ENABLED and request.session.get(SESSION_KEY) and settings.ASPM_OIDC_PROVIDER_LOGOUT:
        endpoint, _ = options()
        query = urlencode({
            "client_id": settings.ASPM_OIDC_CLIENT_ID,
            "post_logout_redirect_uri": settings.SITE_URL.rstrip("/") + settings.LOGIN_URL,
        })
        destination = f"{endpoint}/logout?{query}"
    logout(request)
    return redirect(destination)
