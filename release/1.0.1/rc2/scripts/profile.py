"""Run inside manage.py shell; credentials on stdin, parameters via environment."""
import hashlib
import json
import os
import re
import sys
import time

from django.conf import settings
from django.db import connection
from django.test import Client
from django.test.utils import setup_test_environment
from django.urls import reverse

setup_test_environment()
accounts = json.load(sys.stdin)
scenarios = json.loads(open('/tmp/r4-scenarios.json').read())
variant = os.environ.get('DD_FINAL_VARIANT', 'unknown')
opt_in = {'products_count', 'products_none', 'fast_offset'}
for actor, account in [('admin', accounts[0]), ('restricted', accounts[1]), ('medium', accounts[9]), ('small', accounts[17])]:
    for name, scenario in scenarios.items():
        if variant == 'original' and name in opt_in:
            continue
        client = Client(HTTP_HOST='localhost', raise_request_exception=False)
        headers = {}
        if scenario['auth'] == 'token':
            headers['HTTP_AUTHORIZATION'] = 'Token ' + account['token']
        else:
            client.cookies[settings.SESSION_COOKIE_NAME] = account['session']
        url = scenario['url'].format(**account, nonce='profile-measure')
        client.get(scenario['url'].format(**account, nonce='profile-warmup'), secure=True, **headers)
        queries = []
        def measure(execute, sql, params, many, context):
            start = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                queries.append((sql, params, (time.perf_counter() - start) * 1000))
        start = time.perf_counter()
        with connection.execute_wrapper(measure):
            response = client.get(url, secure=True, **headers)
        elapsed = (time.perf_counter() - start) * 1000
        body = response.content
        row = dict(variant=variant, actor=actor, case=name, url=url, status=response.status_code,
                   wall_ms=elapsed, sql_count=len(queries), sql_ms=sum(q[2] for q in queries), bytes=len(body))
        if 'application/json' in response.get('Content-Type', ''):
            payload = json.loads(body)
            row['payload_hash'] = hashlib.sha256(body).hexdigest()
            if isinstance(payload, dict) and isinstance(payload.get('results'), list):
                row['count'] = payload.get('count')
                row['rows'] = len(payload['results'])
                row['ids'] = [r.get('id') for r in payload['results'] if isinstance(r, dict)]
        else:
            normalized = re.sub(rb'(name="csrfmiddlewaretoken" value=")[^"]+', rb'\1<csrf>', body)
            row['html_hash_without_csrf'] = hashlib.sha256(normalized).hexdigest()
            context = response.context
            semantic = {}
            if context is not None:
                for key in ('findings', 'engagements', 'tests'):
                    page = context.get(key)
                    if hasattr(page, 'paginator'):
                        semantic[key+'_count'] = page.paginator.count
                        semantic[key+'_page_size'] = page.paginator.per_page
                        semantic[key+'_ids'] = [o.pk for o in page]
                        semantic[key+'_page'] = page.number
                        objects=list(page)
                        qs=page.object_list
                        original_filter=context.get('filtered')
                        original_qs=getattr(original_filter,'qs',None)
                        # Finding prefetch rebuilds an already evaluated queryset;
                        # its SQL ordering does not describe the cached page rows.
                        if original_qs is not None and hasattr(original_qs,'query'):
                            qs=original_qs
                            semantic[key+'_sort_source']='filtered.qs before pagination/prefetch'
                        else:
                            semantic[key+'_sort_source']='page queryset'
                        ordering=(qs.query.order_by or qs.model._meta.ordering or ()) if hasattr(qs,'query') else (objects[0]._meta.ordering or ()) if objects else ()
                        fields=[field for field in ordering if isinstance(field,str) and field.lstrip('-') not in ('pk','id')]
                        def field_value(obj,field):
                            for part in field.lstrip('-').split('__'):
                                obj=getattr(obj,part)
                            return obj
                        semantic[key+'_sort_fields']=fields
                        semantic[key+'_sort_values']=[[field_value(obj,field) for field in fields] for obj in objects]
                for key in ('engagement_count', 'finding_count', 'mitigated_count', 'accepted_count', 'critical', 'high', 'medium', 'low', 'info', 'by_month', 'punchcard', 'ticks'):
                    value = context.get(key)
                    if value is not None:
                        semantic[key] = value
                page = context.get('prod_list')
                if page is not None:
                    semantic['products'] = [{'id':p.pk, 'count':p.findings_count, 'active':p.active_finding_count, 'verified':p.active_verified_finding_count} for p in page]
                    semantic['total_products'] = page.paginator.count
                if name in {'simple_metrics', 'simple_metrics_cold'}:
                    semantic['metrics'] = {str(pt.pk):values for pt,values in context.get('findings', {}).items()}
            row['semantic'] = semantic
        if name in {'simple_metrics', 'simple_metrics_cold'}:
            row['metrics_cells'] = re.findall(rb'<td class="text-end">\s*([0-9,]+)\s*</td>', body)
            row['metrics_cells'] = [x.decode() for x in row['metrics_cells']]
        print('PROFILE ' + json.dumps(row, default=str), flush=True)
        if actor == 'admin' and name in {'dashboard', 'web_products', 'simple_metrics', 'simple_metrics_cold', 'filtered_product', 'offset', 'web_findings', 'web_test'}:
            for sql, params, ms in sorted(queries, key=lambda q:q[2], reverse=True)[:2]:
                if ms < 25 or not sql.lstrip().startswith('SELECT') or re.search(r'\b(authtoken_token|django_session)\b',sql):
                    continue
                with connection.cursor() as cursor:
                    cursor.execute('EXPLAIN (ANALYZE, BUFFERS, TIMING OFF) ' + sql, params)
                    plan = '\n'.join(row[0] for row in cursor.fetchall())
                shape = re.sub(r"'(?:[^']|'')*'", "'?'", ' '.join(sql.split()))
                print('PLAN ' + json.dumps(dict(variant=variant, case=name, sql=shape, query_ms=ms, plan=plan)), flush=True)
