"""Measure the outer Django request without inspecting bodies or identities."""
from time import monotonic

from django.conf import settings
from prometheus_client import Counter, Gauge, Histogram

from dojo.aspm_observability.metrics import BYTE_BUCKETS, IDENTITY, WEB_BUCKETS

REQUESTS = Counter("aspm_http_requests_total", "Django responses", ["group", "method", "status"])
LATENCY = Histogram("aspm_http_request_duration_seconds", "Time until Django returns a response", ["group", "method", "route"], buckets=WEB_BUCKETS)
SIZE = Histogram("aspm_http_response_bytes", "Response size when known at response creation", ["group"], buckets=BYTE_BUCKETS)
ACCEPTANCE = Histogram("aspm_ingestion_acceptance_seconds", "Django request latency for new ScanRun HTTP 202", buckets=WEB_BUCKETS)
IN_FLIGHT = Gauge("aspm_http_in_flight", "Django requests currently handled", multiprocess_mode="livesum")
METHODS = {"GET", "POST", "HEAD", "OPTIONS", "DELETE", "PATCH", "PUT"}


def route_group(path, route):
    if route in {"aspm_v1:report-download", "aspm_v1:artifact"}:
        return "download"
    if path.startswith(("health/", "django_metrics/")):
        return "internal"
    if path.startswith("api/aspm/"):
        return "ingestion"
    if path.startswith("api/v2/"):
        return "api_v2"
    if path.startswith("api/v3/"):
        return "api_v3"
    return "ui"


class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.prefix = settings.URL_PREFIX.strip("/") + "/" if settings.URL_PREFIX.strip("/") else ""

    def __call__(self, request):
        start = monotonic()
        with IN_FLIGHT.track_inprogress():
            response = self.get_response(request)
        elapsed = monotonic() - start
        path = request.path_info.lstrip("/").removeprefix(self.prefix)
        match = getattr(request, "resolver_match", None)
        route = match.view_name if match else "unresolved"
        group = route_group(path, route)
        method = request.method if request.method in METHODS else "OTHER"
        status = response.status_code
        REQUESTS.labels(group, method, str(status)).inc()
        LATENCY.labels(group, method, route).observe(elapsed)
        length = response.get("Content-Length")
        if length and length.isdecimal():
            SIZE.labels(group).observe(int(length))
        elif not response.streaming:
            SIZE.labels(group).observe(len(response.content))
        if status == 403:
            IDENTITY.labels("permission", "denied").inc()
        if route == "aspm_oidc_login" and 300 <= status < 400:
            IDENTITY.labels("oidc_login", "started").inc()
        if route == "aspm_oidc_callback":
            IDENTITY.labels("oidc_callback", "success" if 300 <= status < 400 else "failure").inc()
        if (route, method, status) == ("aspm_v1:scans", "POST", 202):
            ACCEPTANCE.observe(elapsed)
        return response
