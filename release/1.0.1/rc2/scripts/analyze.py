"""Pool raw successful observations; keep every run, error and resource window visible."""
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1];M=R
groups=defaultdict(list)
paths=sorted([*(M/'raw').glob('mixed-r*-*-c*-mixed.json'),*(M/'raw').glob('endpoints-r*-*-c1-*.json')])
assert len(paths)==105, 'Expected 45 mixed and 60 dedicated endpoint runs'
for p in paths:
 d=json.loads(p.read_text())
 if d.get('stopped') or d.get('error_rate'):raise RuntimeError('Incomplete measured run: '+p.name)
 groups[(d['variant'],d['phase'],d['concurrency'],d['scenario'])].append((p,d))
rows=[]
def q(values,f):
 s=sorted(values);return s[math.ceil(len(s)*f)-1] if s else None
for (variant,phase,c,case),runs in groups.items():
 samples=[x for _,d in runs for x in d['samples']];lat=[s['ms'] for s in samples];elapsed=sum(d['elapsed_s'] for _,d in runs)
 row=dict(variant=variant,phase=phase,concurrency=c,case=case,n=len(samples),repeats=len(runs),p50_ms=statistics.median(lat),p90_ms=q(lat,.9),p95_ms=q(lat,.95) if len(lat)>=20 else None,p99_ms=q(lat,.99) if len(lat)>=300 else None,rps=len(samples)/elapsed,statuses=dict(Counter(s['status'] for s in samples)),mean_bytes=statistics.mean(s['bytes'] for s in samples),median_sql_count=statistics.median(s['sql_count'] for s in samples),mean_sql_ms=statistics.mean(s['sql_ms'] for s in samples),runs=[])
 metrics=[];rss=[];deltas=[]
 for path,d in runs:
  prefix=path.stem
  row['runs'].append({k:d[k] for k in ('rep','requests','started_at','ended_at','elapsed_s','p50_ms','p90_ms','p95_ms','rps','source_sha','image_id')})
  row['runs'][-1]['mean_sql_ms']=statistics.mean(x['sql_ms'] for x in d['samples'])
  row['runs'][-1]['median_sql_count']=statistics.median(x['sql_count'] for x in d['samples'])
  for suffix,dest in [('-metrics.jsonl',metrics),('-rss.jsonl',rss)]:
   p=M/'raw'/(prefix+suffix)
   if p.exists():
    selected=[x for line in p.read_text().splitlines() if line.strip() and (x:=json.loads(line)) and d['started_at']<=x['at']<=d['ended_at']]
    dest.extend(selected)
    if suffix=='-metrics.jsonl':
     cpus=[x['services']['django-defectdojo-postgres-1']['cpu'] for x in selected if 'services' in x]
     row['runs'][-1]['pg_cpu_mean_pct']=statistics.mean(cpus) if cpus else None
    else:
     row['runs'][-1]['worker_rss_peak_mib']=max((x['rss_max_kib']/1024 for x in selected),default=None)
    pg_window=[x['pg'] for x in selected if 'pg' in x and (phase!='final' or x.get('database')=='dd_round4_seed')] if suffix=='-metrics.jsonl' else []
    if len(pg_window)>=2:deltas.append({k:pg_window[-1][k]-pg_window[0][k] for k in ('blks_hit','blks_read','temp_bytes')})
 valid_pg=[x for x in metrics if phase!='final' or x.get('database')=='dd_round4_seed']
 assert all(x.get('database')=='dd_round4_seed' for x in metrics), 'Wrong database resource scope'
 pg=[x['services']['django-defectdojo-postgres-1']['cpu'] for x in metrics if 'services'in x]
 app=[x['services']['aspm-rc2-aspm-1']['cpu'] for x in metrics if 'services'in x]
 row.update(resource_samples=len(metrics),pg_cpu_mean_pct=statistics.mean(pg) if pg else None,pg_cpu_max_pct=max(pg,default=None),app_cpu_mean_pct=statistics.mean(app) if app else None,worker_rss_peak_mib=max((x['rss_max_kib']/1024 for x in rss),default=None),rss_workers_observed=sorted({x['workers'] for x in rss}),pg_connections_max=max((x['pg']['connections'] for x in valid_pg if 'pg'in x),default=None),celery_queue_max=max((x['celery_queue'] for x in metrics if 'celery_queue'in x),default=None))
 row['pg_scope_excluded_samples']=len(metrics)-len(valid_pg)
 row['pg_sampled_counter_deltas']=deltas
 row['monitor_errors']=sum('monitor_error' in x for x in metrics)
 row['app_container_peak_mib']=max((x['services']['aspm-rc2-aspm-1']['memory_bytes']/1024**2 for x in metrics if 'services' in x),default=None)
 row['worker_rss_sum_peak_mib']=max((x['rss_sum_kib']/1024 for x in rss),default=None)
 row['by_case']={}
 for name in sorted({s['case'] for s in samples}):
  xs=[s for s in samples if s['case']==name];ms=[s['ms'] for s in xs];row['by_case'][name]={'n':len(xs),'p50_ms':statistics.median(ms),'p95_ms':q(ms,.95) if len(ms)>=20 else None,'latency_sum_ms':sum(ms),'mean_bytes':statistics.mean(s['bytes'] for s in xs),'median_sql_count':statistics.median(s['sql_count'] for s in xs),'mean_sql_ms':statistics.mean(s['sql_ms'] for s in xs)}
  row['by_case'][name].update(p90_ms=q(ms,.9),p99_ms=q(ms,.99) if len(ms)>=300 else None,rps_contribution=len(xs)/elapsed)
 rows.append(row)
(R/'benchmark_results.json').write_text(json.dumps(rows,indent=2)+'\n')
columns=['variant','phase','concurrency','case','n','repeats','p50_ms','p90_ms','p95_ms','p99_ms','rps','mean_bytes','median_sql_count','mean_sql_ms','resource_samples','pg_cpu_mean_pct','app_cpu_mean_pct','worker_rss_peak_mib','pg_connections_max']
with (R/'benchmark_results.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,columns,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(rows)
print('Summarized',len(rows),'scenarios;',sum(x['n'] for x in rows),'measured requests')
