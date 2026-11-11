"""Pool request samples; keep individual replicate values and resource windows."""
import csv
import json
import math
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def quantile(values,q):
    v=sorted(values)
    return v[math.ceil(len(v)*q)-1] if v else None

def load_lines(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []

groups={};resource_windows=[]
for path in sorted((ROOT/'raw').glob('*-c*-*.json')):
    if not path.name.startswith(('mixed-','endpoints-')): continue
    d=json.loads(path.read_text())
    assert not d['stopped'] and d['error_rate']==0,path
    metrics=load_lines(ROOT/'raw'/(path.name.split('-c')[0]+'-metrics.jsonl'))
    metrics=[x for x in metrics if d['started_at']<=x['at']<=d['ended_at']]
    rss=load_lines(ROOT/'raw'/(path.name.split('-c')[0]+'-rss.jsonl'))
    rss=[x for x in rss if d['started_at']<=x['at']<=d['ended_at']]
    pg_window=[x['pg'] for x in metrics if 'pg' in x]
    resource_windows.append({'file':path.name,'variant':d['variant'],'phase':d['phase'],'concurrency':d['concurrency'],'scenario':d['scenario'],'n_samples':len(metrics),'pg_reads_delta_sampled_window':pg_window[-1]['blks_read']-pg_window[0]['blks_read'] if len(pg_window)>1 else None,'pg_hits_delta_sampled_window':pg_window[-1]['blks_hit']-pg_window[0]['blks_hit'] if len(pg_window)>1 else None,'pg_temp_bytes_delta_sampled_window':pg_window[-1]['temp_bytes']-pg_window[0]['temp_bytes'] if len(pg_window)>1 else None,'pg_cpu_peak':max((x['services']['django-defectdojo-postgres-1']['cpu'] for x in metrics if 'services' in x),default=None),'pg_active_peak':max((x['active'] for x in pg_window),default=None),'pg_io_wait_peak':max((x['io_wait'] for x in pg_window),default=None),'pg_lock_wait_peak':max((x['lock_wait'] for x in pg_window),default=None),'celery_queue_peak':max((x['celery_queue'] for x in metrics if 'celery_queue' in x),default=None)})
    for case in ['ALL']+sorted({s['case'] for s in d['samples']}):
        samples=[s for s in d['samples'] if case=='ALL' or s['case']==case]
        key=(d['variant'],d['phase'],d['concurrency'],case)
        g=groups.setdefault(key,{'samples':[],'elapsed_s':0,'runs':[],'metrics':[],'rss':[]})
        g['samples']+=samples;g['elapsed_s']+=d['elapsed_s'];g['metrics']+=metrics;g['rss']+=rss
        g['runs'].append({'file':path.name,'n':len(samples),'p95_ms':quantile([s['ms'] for s in samples],.95),'rps':len(samples)/d['elapsed_s'],'seed':d['seed'],'pg_cpu_mean':statistics.mean(x['services']['django-defectdojo-postgres-1']['cpu'] for x in metrics if 'services' in x) if metrics else None})
rows=[]
for (v,phase,c,case),g in groups.items():
    s=g['samples'];lat=[r['ms'] for r in s];sql=[r['sql_ms'] for r in s]
    cpus=[x['services']['django-defectdojo-postgres-1']['cpu'] for x in g['metrics'] if 'services' in x]
    wc=[x['services']['dd-r5-web-1']['cpu'] for x in g['metrics'] if 'services' in x]
    rss=[x['rss_max_kib']/1024 for x in g['rss']]
    pg=[x['pg'] for x in g['metrics'] if 'pg' in x]
    web_memory=[x['services']['dd-r5-web-1']['memory_bytes']/1024**2 for x in g['metrics'] if 'services' in x]
    rss_scope='all workers' if g['rss'] and all(x.get('scope')=='all_workers_by_procname' for x in g['rss']) else 'lower bound: legacy sampler omitted PID1 in some/all runs'
    pg_memory=[x['services']['django-defectdojo-postgres-1']['memory_bytes']/1024**2 for x in g['metrics'] if 'services' in x]
    rows.append(dict(variant=v,phase=phase,concurrency=c,case=case,n=len(s),repeats=len(g['runs']),p50_ms=statistics.median(lat),p90_ms=quantile(lat,.9),p95_ms=quantile(lat,.95) if len(lat)>=20 else None,p99_ms=quantile(lat,.99) if len(lat)>=300 else None,rps=len(s)/g['elapsed_s'],errors=sum(x['status']!='200' for x in s),sql_count_median=statistics.median(x['sql_count'] for x in s),sql_ms_median=statistics.median(sql),sql_ms_sum=sum(sql),latency_ms_sum=sum(lat),response_bytes_median=statistics.median(x['bytes'] for x in s),pg_cpu_mean=statistics.mean(cpus) if cpus else None,web_cpu_mean=statistics.mean(wc) if wc else None,worker_rss_peak_mib=max(rss,default=None),worker_rss_scope=rss_scope,web_container_memory_peak_mib=max(web_memory,default=None),pg_container_memory_peak_mib=max(pg_memory,default=None),pg_connections_peak=max((x['connections'] for x in pg),default=None),runs=g['runs']))
for variant,name in [('original','original.json'),('round4','baseline.json'),('round5','after.json')]:
    (ROOT/name).write_text(json.dumps([r for r in rows if r['variant']==variant],indent=2)+'\n')
(ROOT/'resource_windows.json').write_text(json.dumps(resource_windows,indent=2)+'\n')
(ROOT/'benchmark_results.json').write_text(json.dumps(rows,indent=2)+'\n')
if rows:
    with (ROOT/'benchmark_results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=[k for k in rows[0] if k!='runs'],lineterminator='\n');w.writeheader();w.writerows({k:v for k,v in r.items() if k!='runs'} for r in rows)
for r in rows:
    if r['phase']=='mixed' and r['case']=='ALL':print(r['variant'],r['concurrency'],r['n'],round(r['p95_ms']),round(r['rps'],2),round(r['pg_cpu_mean'] or 0))
