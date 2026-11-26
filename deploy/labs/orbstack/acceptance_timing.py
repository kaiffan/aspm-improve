"""WSGI instrumentation for a disposable lab image.

Append wrap(application) to dojo/wsgi.py in the diagnostic image. Timing headers
are emitted only for the scan upload route. No application identifiers, query
text, credential details or request bytes are returned or stored.
"""
from collections import defaultdict
from contextvars import ContextVar
from functools import wraps
from time import perf_counter, thread_time

from django.db import connection

from dojo.aspm_ingestion import services
from dojo.aspm_ingestion.api import views

trace = ContextVar("aspm_lab_trace", default=None)


def time_calls(owner, name, phase):
    original = getattr(owner, name)

    @wraps(original)
    def measured(*args, **kwargs):
        current = trace.get()
        if current is None:
            return original(*args, **kwargs)
        start = perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            current[phase] += perf_counter() - start

    setattr(owner, name, measured)


def time_sql(execute, sql, params, many, context):
    start = perf_counter()
    try:
        return execute(sql, params, many, context)
    finally:
        elapsed = perf_counter() - start
        current = trace.get()
        current["db_total"] += elapsed
        statement = sql.lower()
        if "for update" in statement or "pg_advisory_" in statement:
            current["db_lock_queries"] += elapsed
        if "aspm_ingestion_rate" in statement:
            current["rate_limit"] += elapsed
        elif ("dojo_repository" in statement or "dojo_commit" in statement) and "dojo_ingestiontoken" not in statement:
            current["repository_commit_sql"] += elapsed
        elif "dojo_scanrun" in statement:
            current["scanrun_sql"] += elapsed
        elif "dojo_ingestionjob" in statement:
            current["outbox_sql"] += elapsed


def wrap(application):
    from rest_framework.request import Request

    for spec in (
        (views.AspmView, "perform_authentication", "authentication"),
        (views.AspmView, "check_permissions", "rbac_view"),
        (views, "require_scope", "rbac_scope"),
        (services, "require_scope", "rbac_scope"),
        (services, "token_repository", "rbac_scope"),
        (Request, "_load_data_and_files", "multipart"),
        (views.ScanUploadSerializer, "is_valid", "validation"),
        (services, "save_original", "artifact_storage"),
        (services, "resolve_engagement", "engagement"),
        (services, "wake_dispatcher", "outbox_wake"),
        (views, "accept_scan", "accept_transaction"),
        (views.ScanRunSerializer, "to_representation", "serialization"),
        (views.ScanUploadView, "post", "post"),
    ):
        time_calls(*spec)

    def handle(environ, start_response):
        if environ.get("REQUEST_METHOD") != "POST" or environ.get("PATH_INFO") != "/api/aspm/v1/scans/":
            return application(environ, start_response)
        values = defaultdict(float)
        token = trace.set(values)
        start = perf_counter()
        cpu_start = thread_time()

        def timed_response(status, headers, exc_info=None):
            values["django"] = perf_counter() - start
            values["request_thread_cpu"] = thread_time() - cpu_start
            header = ", ".join(f"{key};dur={value * 1000:.3f}" for key, value in sorted(values.items()))
            return start_response(status, [*headers, ("Server-Timing", header)], exc_info)

        try:
            with connection.execute_wrapper(time_sql):
                return application(environ, timed_response)
        finally:
            trace.reset(token)

    return handle
