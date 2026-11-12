"""Validation-only Celery instrumentation. No arguments, results or secrets logged."""
import datetime
import json
import os
import resource
import time
from celery.signals import before_task_publish, task_postrun, task_prerun

_started={}


@before_task_publish.connect(weak=False)
def published(headers=None, **kwargs):
    if headers is not None:headers['rc3_published_at']=time.time()


@task_prerun.connect(weak=False)
def starting(task_id=None, task=None, **kwargs):
    now=time.time()
    usage=resource.getrusage(resource.RUSAGE_SELF)
    headers=getattr(task.request,'headers',None) or {}
    sent=headers.get('rc3_published_at',getattr(task.request,'rc3_published_at',None))
    eta=getattr(task.request,'eta',None)
    eligible=datetime.datetime.fromisoformat(eta.replace('Z','+00:00')).timestamp() if eta else sent
    _started[task_id]=dict(started_at=now,clock=time.perf_counter(),cpu=usage.ru_utime+usage.ru_stime,
        published_at=sent,eta=eta,queue_eligible_wait_ms=max(0,now-max(sent,eligible))*1000 if sent is not None and eligible is not None else None)


@task_postrun.connect(weak=False)
def finished(task_id=None, task=None, state=None, **kwargs):
    start=_started.pop(task_id,None)
    if start is None:return
    usage=resource.getrusage(resource.RUSAGE_SELF)
    row=dict(task=task.name,task_id=task_id,state=state,pid=os.getpid(),
        execution_ms=(time.perf_counter()-start.pop('clock'))*1000,
        cpu_ms=(usage.ru_utime+usage.ru_stime-start.pop('cpu'))*1000,
        process_peak_rss_kib=usage.ru_maxrss,**start)
    fd=os.open('/tmp/rc3-task-metrics.jsonl',os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
    try:os.write(fd,(json.dumps(row)+'\n').encode())
    finally:os.close(fd)
