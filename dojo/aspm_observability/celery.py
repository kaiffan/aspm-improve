"""Observe Celery in-process without broadcast inspect or task identities in series."""
import time

from celery import signals
from celery.worker import state
from prometheus_client import Counter, Gauge, Histogram

from dojo.aspm_observability.metrics import JOB_BUCKETS

TASKS = {
    "dojo.aspm_ingestion.dispatch_jobs": "dispatch",
    "dojo.aspm_ingestion.process_job": "ingestion",
    "dojo.webhooks.deliver": "webhook",
}
PUBLISH = Counter("aspm_celery_published_total", "Successfully published Celery tasks", ["task"])
OUTCOME = Counter("aspm_celery_tasks_total", "Celery task execution results", ["task", "result"])
RUNTIME = Histogram("aspm_celery_task_seconds", "Celery task execution duration", ["task"], buckets=JOB_BUCKETS)
HEARTBEAT = Gauge("aspm_celery_heartbeat_timestamp_seconds", "Last worker heartbeat", multiprocess_mode="max")
INVENTORY = Gauge("aspm_celery_worker_tasks", "Worker inventory at last heartbeat", ["state"], multiprocess_mode="mostrecent")


def task_group(name):
    return TASKS.get(name, "other")


@signals.heartbeat_sent.connect
def on_heartbeat(**kwargs):
    HEARTBEAT.set(time.time())
    INVENTORY.labels("active").set(len(state.active_requests))
    INVENTORY.labels("reserved").set(len(state.reserved_requests - state.active_requests))


@signals.after_task_publish.connect
def on_publish(sender=None, **kwargs):
    PUBLISH.labels(task_group(sender)).inc()


@signals.task_prerun.connect
def on_start(sender=None, **kwargs):
    sender.request.aspm_metric_started = time.monotonic()


@signals.task_postrun.connect
def on_finish(sender=None, state=None, **kwargs):
    task = task_group(sender.name)
    if (started := getattr(sender.request, "aspm_metric_started", None)) is not None:
        RUNTIME.labels(task).observe(time.monotonic() - started)
    result = {"SUCCESS": "success", "FAILURE": "failure", "RETRY": "retry", "REVOKED": "revoked"}
    OUTCOME.labels(task, result.get(state, "other")).inc()
