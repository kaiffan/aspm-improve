"""Bounded event metrics for the ASPM runtime."""
import os
from collections.abc import Callable
from functools import wraps
from time import monotonic

from prometheus_client import Counter, Histogram

from dojo.aspm_ingestion.scanners import SCANNER_FORMATS

ENABLED = os.environ.get("DD_ASPM_OBSERVABILITY") == "true"
WEB_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120)
JOB_BUCKETS = (0.05, 0.25, 1, 2.5, 5, 10, 30, 60, 90, 110, 180, 300, 600, 900, 1800)
BYTE_BUCKETS = (1024, 16384, 131072, 1048576, 8388608, 33554432, 67108864)
SCANNERS = {value: key.lower() for key, value, _ in SCANNER_FORMATS}
EVENTS = Counter("aspm_scan_events_total", "Durable scan lifecycle events", ["scanner", "result"])
SCAN_PHASE = Histogram("aspm_scan_phase_seconds", "Scan phase duration", ["scanner", "stage"], buckets=JOB_BUCKETS)
FINDINGS = Counter("aspm_scan_findings_imported_total", "New findings created by completed imports", ["scanner"])
OBSERVATIONS = Counter("aspm_scan_observations_total", "Observations published by completed scans", ["scanner"])
ARTIFACT_SIZE = Histogram("aspm_artifact_bytes", "Size of a committed artifact", ["format"], buckets=BYTE_BUCKETS)
REPORTS = Counter("aspm_report_events_total", "Report lifecycle events", ["kind", "result"])
REPORT_PHASE = Histogram("aspm_report_phase_seconds", "Report phase duration", ["kind", "stage"], buckets=JOB_BUCKETS)
STORAGE_FAILURES = Counter("aspm_storage_failures_total", "Private evidence operation failures", ["operation"])
DISPATCH = Counter("aspm_outbox_dispatch_total", "Attempts to publish durable jobs to the broker", ["kind", "result"])
WEBHOOK_STATUS = Counter("aspm_webhook_http_total", "Webhook HTTP attempts grouped by response class", ["status_class"])
WEBHOOK_WAIT = Histogram("aspm_webhook_queue_wait_seconds", "Time from delivery creation to first HTTP attempt", buckets=JOB_BUCKETS)
IDENTITY = Counter("aspm_identity_events_total", "OIDC and managed session outcomes", ["event", "result"])

for _scanner in (*SCANNERS.values(), "other"):
    for _result in ("accepted", "duplicate", "completed", "failed", "retry", "recovered"):
        EVENTS.labels(_scanner, _result)
for _kind in ("generated", "classic"):
    for _result in ("requested", "generated", "failed", "download_failed", "integrity_failed", "size_limit"):
        REPORTS.labels(_kind, _result)
for _event, _results in {
    "oidc_callback": ("success", "failure"),
    "oidc_login": ("started",),
    "provider": ("unavailable",),
    "permission": ("denied",),
    "session": ("expired",),
}.items():
    for _result in _results:
        IDENTITY.labels(_event, _result)


def scan_event(scanner, result):
    if ENABLED:
        EVENTS.labels(SCANNERS.get(scanner, "other"), result).inc()


def report_event(result, kind="generated"):
    if ENABLED:
        REPORTS.labels(kind, result).inc()


def timed_report(kind):
    def decorator(view: Callable):
        @wraps(view)
        def measured(*args, **kwargs):
            if not ENABLED:
                return view(*args, **kwargs)
            start = monotonic()
            report_event("requested", kind)
            try:
                response = view(*args, **kwargs)
            except Exception:
                report_event("failed", kind)
                raise
            report_event("generated" if response.status_code < 400 else "failed", kind)
            REPORT_PHASE.labels(kind, "generation").observe(monotonic() - start)
            return response

        return measured

    return decorator
