"""Run inside Django shell with private accounts on stdin; no bindings are output."""
from contextlib import ExitStack
import gc
import json
import re
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.db import connection
from django.db.models.query import QuerySet
from django.template.backends.django import Template
from django.test import Client
from rest_framework.renderers import JSONRenderer

import dojo.home.views as home
from dojo.product.api.serializer import ProductSerializer
from dojo.product.api.views import ProductViewSet

accounts = json.load(sys.stdin)

def rss():
    return int(next(line.split()[1] for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('VmRSS:'))) * 1024

for ai in [0,1,9,17]:
    account = accounts[ai]
    for name,url in [('products','/api/v2/products/?limit=100'),('web_products','/asset'),('dashboard','/dashboard'),('web_findings','/finding/open'),('web_test',f'/test/{account["test"]}')]:
        if ai not in [0,1] and name in ['web_findings','web_test']: continue
        gc.collect()
        timings = {}; queries = []; memory = [rss()]; stop = threading.Event()
        def sample():
            while not stop.wait(.01): memory.append(rss())
        thread=threading.Thread(target=sample); thread.start()
        def timed(key,fn):
            def inner(*a,**kw):
                t=time.perf_counter(); before=sum(q[2] for q in queries)
                try:return fn(*a,**kw)
                finally:
                    timings[key]=timings.get(key,0)+(time.perf_counter()-t)*1000
                    timings[key+"_sql_subset"]=timings.get(key+"_sql_subset",0)+sum(q[2] for q in queries)-before
            return inner
        def measure(execute,sql,params,many,context):
            t=time.perf_counter()
            try:return execute(sql,params,many,context)
            finally:queries.append((sql,params,(time.perf_counter()-t)*1000))
        client=Client(HTTP_HOST='localhost',HTTP_AUTHORIZATION='Token '+account['token'],raise_request_exception=False)
        client.cookies[settings.SESSION_COOKIE_NAME]=account['session']
        t=time.perf_counter()
        with ExitStack() as stack:
            if hasattr(ProductViewSet,'_load_findings_fields'):stack.enter_context(patch.object(ProductViewSet,'_load_findings_fields',timed('product_id_loading_ms',ProductViewSet._load_findings_fields)))
            stack.enter_context(patch.object(ProductSerializer,'to_representation',timed('product_representation_ms',ProductSerializer.to_representation)))
            stack.enter_context(patch.object(JSONRenderer,'render',timed('json_render_ms',JSONRenderer.render)))
            stack.enter_context(patch.object(Template,'render',timed('template_inclusive_ms',Template.render)))
            for key in ['get_dashboard_chart_data','get_severities_all','get_severities_by_month','get_punchcard_data']:
                if hasattr(home,key):stack.enter_context(patch.object(home,key,timed(key+'_ms',getattr(home,key))))
            depth=[0];fetch=QuerySet._fetch_all;fetch_timed=timed('queryset_evaluation_inclusive_ms',fetch)
            def fetch_all(instance):
                depth[0]+=1
                try:return fetch_timed(instance) if depth[0]==1 else fetch(instance)
                finally:depth[0]-=1
            stack.enter_context(patch.object(QuerySet,'_fetch_all',fetch_all))
            stack.enter_context(connection.execute_wrapper(measure))
            response=client.get(url,secure=True)
        wall=(time.perf_counter()-t)*1000
        memory.append(rss());stop.set();thread.join()
        row={'actor':ai,'case':name,'status':response.status_code,'wall_ms':wall,'sql_ms':sum(q[2] for q in queries),'sql_count':len(queries),'bytes':len(response.content),'phases':timings,'rss_before':memory[0],'rss_peak_sampled':max(memory),'rss_after':memory[-1],'queries':[]}
        if name=='products' and response.status_code==200:
            data=response.json()['results'];row['finding_ids']=sum(len(p['findings_list']) for p in data)
        for sql,params,ms in queries:
            if 'dojo_finding' not in sql or not sql.startswith('SELECT') or ms<35:continue
            with connection.cursor() as cursor:
                cursor.execute('EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, FORMAT JSON) '+sql,params);plan=cursor.fetchone()[0]
            row['queries'].append({'sql':re.sub(r"'(?:[^']|'')*'","'<redacted>'",sql),'ms':ms,'plan':plan})
        print('PROFILE '+json.dumps(row,default=str),flush=True)
