"""Isolated background benchmark telemetry; records no task arguments or SQL text."""
import json
import resource
import time

from celery.signals import before_task_publish, task_postrun, task_prerun, task_received, worker_ready
from django.db import connection

running = {}


def emit(**row):
    print('R4_TASK ' + json.dumps(row), flush=True)


@before_task_publish.connect(weak=False)
def published(headers=None, **kwargs):
    if headers is not None:
        headers['r4_published_at'] = time.time()


@task_received.connect(weak=False)
def received(request=None, **kwargs):
    headers = request.request_dict
    emit(event='received', task_id=request.id, at=time.time(), published_at=headers.get('r4_published_at'))


@worker_ready.connect(weak=False)
def ready(**kwargs):
    emit(event='ready', at=time.time())


@task_prerun.connect(weak=False)
def start(task_id=None, task=None, **kwargs):
    data = {'event': 'finished', 'task_id': task_id, 'name': task.name, 'started_at': time.time(), 'sql_count': 0, 'sql_ms': 0.0}
    headers = task.request.headers or {}
    data['published_at'] = headers.get('r4_published_at')
    def measure(execute, sql, params, many, context):
        begin = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            data['sql_count'] += 1
            data['sql_ms'] += (time.perf_counter() - begin) * 1000
    wrapper = connection.execute_wrapper(measure)
    wrapper.__enter__()
    running[task_id] = (data, wrapper, time.perf_counter())


@task_postrun.connect(weak=False)
def finish(task_id=None, state=None, **kwargs):
    if task_id not in running:
        return
    data, wrapper, begin = running.pop(task_id)
    wrapper.__exit__(None, None, None)
    data.update(at=time.time(), duration_ms=(time.perf_counter()-begin)*1000, state=state,
                rss_hwm_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    emit(**data)
