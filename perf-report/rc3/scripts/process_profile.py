"""Diagnostic CPU/allocation snapshots in a separate Django process, not HTTP percentiles."""
import hashlib
import json
import os
import resource
import sys
import time
import tracemalloc
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.test import Client

accounts=json.load(sys.stdin)
scenarios=json.loads(Path('/tmp/r4-scenarios.json').read_text())
scenarios['reports']={'url':'/reports/builder','auth':'session'}
names=['findings','filtered_product','finding_detail','products','tests','engagements','dashboard','web_products','endpoints','web_findings','web_test','reports']


def rss():
    return int(next(line.split()[1] for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('VmRSS:')))


for actor,account in [('admin',accounts[0]),('restricted',accounts[1]),('small',accounts[17])]:
    for name in names:
        client=Client(HTTP_HOST='localhost',raise_request_exception=False)
        scenario=scenarios[name]
        headers={}
        if scenario['auth']=='token':headers['HTTP_AUTHORIZATION']='Token '+account['token']
        else:client.cookies[settings.SESSION_COOKIE_NAME]=account['session']
        url=scenario['url'].format(**account,nonce='allocation')
        client.get(url,secure=True,**headers)
        before_rss=rss()
        count=0
        sql_ms=0.
        def sql(execute,statement,params,many,context):
            global count,sql_ms
            start=time.perf_counter()
            try:return execute(statement,params,many,context)
            finally:count+=1;sql_ms+=(time.perf_counter()-start)*1000
        tracemalloc.start(1)
        usage=resource.getrusage(resource.RUSAGE_SELF)
        cpu_start=usage.ru_utime+usage.ru_stime
        start=time.perf_counter()
        with connection.execute_wrapper(sql):response=client.get(url,secure=True,**headers)
        wall=(time.perf_counter()-start)*1000
        usage=resource.getrusage(resource.RUSAGE_SELF)
        cpu=(usage.ru_utime+usage.ru_stime-cpu_start)*1000
        allocated,peak=tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print('MEMORY '+json.dumps(dict(variant=os.environ['RC3_VARIANT'],actor=actor,case=name,
            status=response.status_code,wall_with_tracing_ms=wall,cpu_with_tracing_ms=cpu,
            rss_before_kib=before_rss,rss_after_kib=rss(),process_peak_rss_kib=usage.ru_maxrss,
            python_allocated_bytes=allocated,python_peak_allocated_bytes=peak,
            sql_count=count,sql_wall_ms=sql_ms,bytes=len(response.content),
            body_sha256=hashlib.sha256(response.content).hexdigest() if scenario['auth']=='token' else None)),flush=True)
