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
        if actor == 'admin' and name in {'dashboard', 'web_products', 'simple_metrics', 'simple_metrics_cold', 'filtered_product', 'offset'}:
            for sql, params, ms in sorted(queries, key=lambda q:q[2], reverse=True)[:2]:
                if ms < 25 or not sql.lstrip().startswith('SELECT'):
                    continue
                with connection.cursor() as cursor:
                    cursor.execute('EXPLAIN (ANALYZE, BUFFERS, TIMING OFF) ' + sql, params)
                    plan = '\n'.join(row[0] for row in cursor.fetchall())
                shape = re.sub(r"'(?:[^']|'')*'", "'?'", ' '.join(sql.split()))
                print('PLAN ' + json.dumps(dict(variant=variant, case=name, sql=shape, query_ms=ms, plan=plan)), flush=True)
