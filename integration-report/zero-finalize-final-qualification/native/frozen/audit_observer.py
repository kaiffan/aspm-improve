# ruff: noqa
# Preserved qualification harness; source hashes are in input/harness-provenance.json.
"""Minimal baseline counters/task correlation; deep SQL/CPU profiling is opt-in separately."""

import contextvars
import functools
import hashlib
import json
import os
import re
import resource
import threading
import time
import traceback
from pathlib import Path

from celery.signals import (
    before_task_publish,
    task_postrun,
    task_prerun,
    task_received,
    task_retry,
)

OP = contextvars.ContextVar("audit_op", default=None)
DEEP = os.getenv("AUDIT_DIAGNOSTIC") == "1"
active = 0
lock = threading.Lock()
task_start = {}
task_sql = {}
task_profiles = {}
installed = False


def record(event, **data):
    folder = Path("/acceptance-telemetry")
    if not folder.exists():
        return
    row = {
        "event": event,
        "at": time.time(),
        "pid": os.getpid(),
        "database": os.getenv("ACCEPTANCE_DATABASE"),
        "role": os.getenv("ACCEPTANCE_ROLE"),
        "opid": OP.get(),
        **data,
    }
    fd = os.open(
        folder
        / (os.getenv("ACCEPTANCE_ROLE", "unknown") + "-" + str(os.getpid()) + ".jsonl"),
        os.O_CREAT | os.O_WRONLY | os.O_APPEND,
        0o666,
    )
    try:
        os.write(fd, (json.dumps(row, default=str) + "\n").encode())
    finally:
        os.close(fd)


@before_task_publish.connect(weak=False)
def publish(headers=None, **kwargs):
    if headers is None:
        return
    headers["audit_opid"] = OP.get()
    headers["audit_published_at"] = time.time()
    record(
        "task_publish",
        task_id=headers.get("id"),
        task=headers.get("task"),
        parent_id=headers.get("parent_id"),
    )


@task_received.connect(weak=False)
def receive(request=None, **kwargs):
    if request is None:
        return
    h = getattr(request, "headers", None) or {}
    # Consumer Request may expose custom headers through request_dict instead.
    h = {**(getattr(request, "request_dict", None) or {}), **h}
    record(
        "task_receive",
        task_id=request.id,
        task=request.name,
        opid=h.get("audit_opid"),
        published_at=h.get("audit_published_at"),
    )


@task_prerun.connect(weak=False)
def prerun(task_id=None, task=None, **kwargs):
    h = getattr(task.request, "headers", None) or {}
    OP.set(h.get("audit_opid"))
    task_start[task_id] = (time.perf_counter(), time.process_time())
    if DEEP:
        import cProfile

        from django.db import connection

        stats = {"count": 0, "sql_ms": 0.0}

        def observed(fn, statement, params, many, context):
            begin = time.perf_counter()
            try:
                return fn(statement, params, many, context)
            finally:
                ms = (time.perf_counter() - begin) * 1000
                stats["count"] += 1
                stats["sql_ms"] += ms
                if statement.lstrip().upper().startswith("SELECT") and not re.search(
                    r"authtoken_token|django_session", statement, re.I
                ):
                    record(
                        "task_sql",
                        task_id=task_id,
                        statement=statement,
                        params=params,
                        ms=ms,
                        stack=[
                            {"file": f.filename, "line": f.lineno, "function": f.name}
                            for f in traceback.extract_stack()
                            if "/dojo/" in f.filename
                        ][-10:],
                    )

        cm = connection.execute_wrapper(observed)
        cm.__enter__()
        task_sql[task_id] = (cm, stats)
        prof = cProfile.Profile()
        prof.enable()
        task_profiles[task_id] = prof
    record(
        "task_start",
        task_id=task_id,
        task=task.name,
        published_at=h.get("audit_published_at"),
    )


@task_postrun.connect(weak=False)
def postrun(task_id=None, task=None, state=None, **kwargs):
    start = task_start.pop(task_id, None)
    sql_stats = {}
    if task_id in task_sql:
        cm, sql_stats = task_sql.pop(task_id)
        cm.__exit__(None, None, None)
    if task_id in task_profiles:
        prof = task_profiles.pop(task_id)
        prof.disable()
        prof.dump_stats("/acceptance-telemetry/task_" + task_id + ".prof")
    record(
        "task_end",
        task_id=task_id,
        task=task.name,
        state=state,
        diagnostic_sql=sql_stats,
        execution_ms=(time.perf_counter() - start[0]) * 1000 if start else None,
        cpu_ms=(time.process_time() - start[1]) * 1000 if start else None,
        max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    )
    OP.set(None)


@task_retry.connect(weak=False)
def retry(request=None, **kwargs):
    record("task_retry", task_id=getattr(request, "id", None))


def wrap(owner, name):
    original = getattr(owner, name, None)
    if not original or getattr(original, "_audit_wrapped", False):
        return

    @functools.wraps(original)
    def call(*args, **kwargs):
        start = time.perf_counter()
        cpu = time.thread_time()
        try:
            return original(*args, **kwargs)
        finally:
            if OP.get():
                record(
                    "phase",
                    name=owner.__module__ + "." + owner.__name__ + "." + name,
                    ms=(time.perf_counter() - start) * 1000,
                    cpu_ms=(time.thread_time() - cpu) * 1000,
                )

    call._audit_wrapped = True
    setattr(owner, name, call)


def install_deep():
    global installed
    if installed or not DEEP:
        return
    installed = True
    from django.template.backends.django import Template
    from rest_framework.serializers import BaseSerializer
    from rest_framework.views import APIView

    for name in [
        "perform_authentication",
        "check_permissions",
        "check_object_permissions",
    ]:
        wrap(APIView, name)
    for name in ["to_representation", "is_valid", "save"]:
        wrap(BaseSerializer, name)
    wrap(Template, "render")
    # Deep-only prefetch entry evidence is emitted before materializing large related sets.
    import django.db.models.query as query_module

    original_prefetch = query_module.prefetch_related_objects

    @functools.wraps(original_prefetch)
    def observed_prefetch(instances, *lookups):
        record(
            "prefetch_start",
            instances=len(instances),
            lookups=[str(x) for x in lookups],
            max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            stack=[
                {"file": f.filename, "line": f.lineno, "function": f.name}
                for f in traceback.extract_stack()
                if "/dojo/" in f.filename
            ][-10:],
        )
        start = time.perf_counter()
        try:
            return original_prefetch(instances, *lookups)
        finally:
            record(
                "prefetch_end",
                instances=len(instances),
                ms=(time.perf_counter() - start) * 1000,
                max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            )

    query_module.prefetch_related_objects = observed_prefetch
    # Function-level authorization is attributed by cProfile and slow-SQL stack, not monkeypatched globally.


class Middleware:
    def __init__(self, get_response):
        self.get_response = get_response
        install_deep()

    def __call__(self, request):
        global active
        from django.db import connection

        op = request.headers.get("X-Acceptance-Operation") or request.headers.get(
            "X-Audit-Operation"
        )
        token = OP.set(op)
        stats = {"count": 0, "wall_ms": 0.0}
        start = time.perf_counter()
        cpu = time.thread_time()
        with lock:
            active += 1
            flight = active
        record(
            "http_start",
            path=request.path,
            method=request.method,
            inflight_in_worker=flight,
        )

        def execute(fn, statement, params, many, context):
            if (
                DEEP
                and op
                and statement.lstrip().upper().startswith("SELECT")
                and not re.search(r"authtoken_token|django_session", statement, re.I)
            ):
                record(
                    "sql_start",
                    statement=statement,
                    params=params,
                    max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                )
            t = time.perf_counter()
            try:
                return fn(statement, params, many, context)
            finally:
                ms = (time.perf_counter() - t) * 1000
                stats["count"] += 1
                stats["wall_ms"] += ms
                if (
                    DEEP
                    and op
                    and ms >= 0
                    and statement.lstrip().upper().startswith("SELECT")
                    and not re.search(
                        r"authtoken_token|django_session", statement, re.I
                    )
                ):
                    record(
                        "sql",
                        ms=ms,
                        statement=statement,
                        params=params,
                        shape_sha256=hashlib.sha256(statement.encode()).hexdigest(),
                        stack=[
                            {"file": f.filename, "line": f.lineno, "function": f.name}
                            for f in traceback.extract_stack()
                            if "/dojo/" in f.filename
                        ][-12:],
                    )

        profile = None
        if DEEP and request.headers.get("X-Audit-Profile") == "1":
            import cProfile

            profile = cProfile.Profile()
            profile.enable()
        try:
            with connection.execute_wrapper(execute):
                response = self.get_response(request)
            response["X-Acceptance-View-Ms"] = str((time.perf_counter() - start) * 1000)
            response["X-Acceptance-SQL-Ms"] = str(stats["wall_ms"])
            response["X-Acceptance-SQL-Count"] = str(stats["count"])
            response["X-Perf-SQL-Ms"] = str(stats["wall_ms"])
            response["X-Perf-SQL-Count"] = str(stats["count"])
            record(
                "http_end",
                path=request.path,
                method=request.method,
                status=response.status_code,
                ms=(time.perf_counter() - start) * 1000,
                cpu_ms=(time.thread_time() - cpu) * 1000,
                sql=stats,
                max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            )
            return response
        finally:
            if profile:
                profile.disable()
                filename = (
                    re.sub("[^a-zA-Z0-9_-]", "_", op or "diagnostic")
                    + "_"
                    + request.method
                    + "_"
                    + hashlib.sha256(request.path.encode()).hexdigest()[:8]
                    + "_"
                    + str(time.time_ns())
                    + ".prof"
                )
                profile.dump_stats("/acceptance-telemetry/" + filename)
                record(
                    "profile_written",
                    file=filename,
                    path=request.path,
                    method=request.method,
                )
            with lock:
                active -= 1
            OP.reset(token)
