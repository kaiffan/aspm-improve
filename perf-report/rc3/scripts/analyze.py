"""Aggregate only the fresh paired cohort; retain per-repeat results and regressions."""
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]
groups=defaultdict(list)
for path in sorted((OUT/'raw').glob('*.json')):
    if path.name.startswith(('campaign-','incremental-','endpoints-')):
        try:row=json.loads(path.read_text())
        except json.JSONDecodeError:continue  # controller metadata is written after benchmark output
        if 'samples' in row and 'phase' in row:
            assert not row['stopped'] and row['error_rate']==0, path.name
            groups[(row['phase'],row['variant'],row['concurrency'],row['scenario'])].append((path,row))


def percentile(values,q,minimum=1):
    values=sorted(values)
    return values[math.ceil(len(values)*q)-1] if len(values)>=minimum else None


def mean(values):
    values=list(values)
    return statistics.mean(values) if values else None


def route_summary(samples,total_ms,slow):
    ms=[s['ms'] for s in samples]
    return dict(n=len(samples),p50_ms=statistics.median(ms),p90_ms=percentile(ms,.9,100),
        p95_ms=percentile(ms,.95,100),p99_ms=percentile(ms,.99,300),mean_ms=mean(ms),
        request_elapsed_ms=sum(ms),request_elapsed_share=sum(ms)/total_ms,
        sql_count_mean=mean(s['sql_count'] for s in samples),sql_count_max=max(s['sql_count'] for s in samples),
        sql_wall_mean_ms=mean(s['sql_ms'] for s in samples),sql_wall_total_ms=sum(s['sql_ms'] for s in samples),
        bytes_mean=mean(s['bytes'] for s in samples),bytes_max=max(s['bytes'] for s in samples),
        slowest_five_percent_count=sum(id(s) in slow for s in samples),
        share_of_slowest_five_percent=sum(id(s) in slow for s in samples)/len(slow) if slow else None)


results=[]
for (phase,variant,c,case),runs in sorted(groups.items()):
    samples=[s for _,run in runs for s in run['samples']]
    ms=[s['ms'] for s in samples]
    elapsed=sum(run['elapsed_s'] for _,run in runs)
    total_ms=sum(ms)
    slow={id(s) for s in sorted(samples,key=lambda s:s['ms'],reverse=True)[:math.ceil(.05*len(samples))]}
    row=dict(phase=phase,variant=variant,concurrency=c,case=case,n=len(samples),repeats=len(runs),
        p50_ms=statistics.median(ms),p90_ms=percentile(ms,.9),p95_ms=percentile(ms,.95),p99_ms=percentile(ms,.99,300),
        rps=len(samples)/elapsed,elapsed_s=elapsed,statuses=dict(Counter(s['status'] for s in samples)),
        sql_count_mean=mean(s['sql_count'] for s in samples),sql_wall_mean_ms=mean(s['sql_ms'] for s in samples),
        response_bytes_mean=mean(s['bytes'] for s in samples),runs=[],by_case={})
    metrics=[]
    rss=[]
    for path,run in runs:
        rr={k:run[k] for k in ['repeat','p50_ms','p90_ms','p95_ms','p99_ms','rps','requests','elapsed_s','image_id']}
        rr['sql_wall_mean_ms']=mean(s['sql_ms'] for s in run['samples'])
        row['runs'].append(rr)
        for suffix,target in [('-metrics.jsonl',metrics),('-rss.jsonl',rss)]:
            p=path.with_name(path.stem+suffix)
            if p.exists():
                target.extend(x for line in p.read_text().splitlines() if line.strip() and (x:=json.loads(line)) and run['started_at']<=x['at']<=run['ended_at'])
    assert all(m.get('database')=='dd_round4_seed' for m in metrics)
    row.update(resource_samples=len(metrics),monitor_errors=sum('monitor_error' in m for m in metrics),
        pg_cpu_mean_pct=mean(m['services']['django-defectdojo-postgres-1']['cpu'] for m in metrics if 'services' in m),
        app_cpu_mean_pct=mean(m['services']['aspm-rc3-aspm-1']['cpu'] for m in metrics if 'services' in m),
        app_rss_peak_mib=max((m['services']['aspm-rc3-aspm-1']['memory_bytes']/1024**2 for m in metrics if 'services' in m),default=None),
        worker_rss_peak_mib=max((m['rss_max_kib']/1024 for m in rss),default=None),
        worker_rss_sum_peak_mib=max((m['rss_sum_kib']/1024 for m in rss),default=None),
        pg_connections_max=max((m['pg']['connections'] for m in metrics if 'pg' in m),default=None),
        pg_lock_wait_samples=sum(m['pg']['lock_wait'] for m in metrics if 'pg' in m),
        pg_io_wait_samples=sum(m['pg']['io_wait'] for m in metrics if 'pg' in m))
    for name in sorted({s['case'] for s in samples}):
        row['by_case'][name]=route_summary([s for s in samples if s['case']==name],total_ms,slow)
    results.append(row)

(OUT/'benchmark_results.json').write_text(json.dumps(results,indent=2)+'\n')
columns=['phase','variant','concurrency','case','n','repeats','p50_ms','p90_ms','p95_ms','p99_ms','rps','sql_count_mean','sql_wall_mean_ms','response_bytes_mean','pg_cpu_mean_pct','app_cpu_mean_pct','app_rss_peak_mib','worker_rss_peak_mib','pg_connections_max','pg_lock_wait_samples','pg_io_wait_samples','resource_samples','monitor_errors']
with (OUT/'benchmark_results.csv').open('w',newline='') as stream:
    writer=csv.DictWriter(stream,columns,extrasaction='ignore',lineterminator='\n')
    writer.writeheader()
    writer.writerows(results)
print('Aggregated',len(results),'groups',sum(r['n'] for r in results),'requests')
