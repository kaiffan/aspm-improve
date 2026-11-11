#!/usr/bin/env python3
"""Build JSON/CSV from request-level observations. Never average p95 values."""
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parent


def quantile(values,q,minimum=1):
    values=sorted(v for v in values if v is not None)
    return round(values[math.ceil(q*len(values))-1],3) if len(values)>=minimum else None


def read_lines(path):
    if not path.exists():return []
    rows=[]
    for line in path.read_text().splitlines():
        try:rows.append(json.loads(line))
        except json.JSONDecodeError:continue
    return rows


def resources(path,result):
    prefix=path.name.rsplit('-c',1)[0]
    if result.get('phase','').startswith('background'):
        prefix='background-'+result['variant']
    samples=[r for r in read_lines(ROOT/'raw'/(prefix+'-metrics.jsonl'))
             if result['started_at']<=r.get('at',0)<=result['ended_at']]
    rss=[r for r in read_lines(ROOT/'raw'/(prefix+'-rss.jsonl'))
         if result['started_at']<=r.get('at',0)<=result['ended_at']]
    def peak(name,key):
        values=[r.get('services',{}).get(name,{}).get(key) for r in samples]
        values=[v for v in values if v is not None]
        return max(values,default=None)
    def delta(key):
        values=[r['pg'][key] for r in samples if key in r.get('pg',{})]
        return max(0,values[-1]-values[0]) if len(values)>=2 else None
    return {'resource_samples':len(samples),'uwsgi_cpu_peak':peak('dd-final-web-1','cpu'),
            'pg_cpu_peak':peak('django-defectdojo-postgres-1','cpu'),
            'uwsgi_container_mib_peak':None if peak('dd-final-web-1','memory_bytes') is None else peak('dd-final-web-1','memory_bytes')/1024**2,
            'pg_container_mib_peak':None if peak('django-defectdojo-postgres-1','memory_bytes') is None else peak('django-defectdojo-postgres-1','memory_bytes')/1024**2,
            'uwsgi_worker_rss_mib_peak':max((r['rss_max_kib']/1024 for r in rss),default=None),
            'pg_connections_peak':max((r.get('pg',{}).get('connections',0) for r in samples),default=None),
            'pg_active_peak':max((r.get('pg',{}).get('active',0) for r in samples),default=None),
            'pg_reads_sampled_delta':delta('blks_read'),'pg_hits_sampled_delta':delta('blks_hit'),
            'pg_temp_bytes_sampled_delta':delta('temp_bytes'),
            'celery_queue_peak':max((r.get('celery_queue',0) for r in samples),default=None)}


def main():
    results=[]
    for path in sorted((ROOT/'raw').glob('*.json')):
        data=json.loads(path.read_text())
        if not isinstance(data,dict) or 'samples' not in data:continue
        if path.name.startswith('background-'):
            if 'warmup' in path.name:continue
            data['phase']='background-'+('control' if path.stem.endswith('control') else 'loaded')
        elif data.get('phase') not in {'endpoints','mixed','users'}:continue
        data['file']='raw/'+path.name
        data['resources']=resources(path,data)
        results.append(data)
    groups=defaultdict(list)
    for result in results:groups[(result['phase'],result['variant'],result['scenario'],result['concurrency'])].append(result)
    summary=[];case_rows=[]
    for (phase,variant,case,c),series in sorted(groups.items()):
        samples=[s for r in series for s in r['samples']]
        good=[s for s in samples if s['status']=='200']
        lat=[s['ms'] for s in good]
        counts=[s['sql_count'] for s in good if s.get('sql_count') is not None]
        sql=[s['sql_ms'] for s in good if s.get('sql_ms') is not None]
        elapsed=sum(r['elapsed_s'] for r in series)
        row={'phase':phase,'variant':variant,'case':case,'concurrency':c,'series':len(series),
             'requests':len(samples),'completed':all(not r['stopped'] for r in series),
             'p50_ms':quantile(lat,.5),'p95_ms':quantile(lat,.95,20),'p99_ms':quantile(lat,.99,300),
             'rps':round(len(samples)/elapsed,3),'error_rate':1-len(good)/len(samples),
             'statuses':dict(Counter(s['status'] for s in samples)),
             'sql_count_median':statistics.median(counts) if counts else None,
             'sql_count_min':min(counts,default=None),'sql_count_max':max(counts,default=None),
             'sql_p50_ms':quantile(sql,.5),'sql_p95_ms':quantile(sql,.95,20),
             'response_bytes_median':statistics.median(s['bytes'] for s in good) if good else None,
             'response_bytes_total':sum(s['bytes'] for s in samples),
             'configured_users':series[0]['configured_users'],
             'observed_users':len({s['actor'] for s in samples}),
             'think_time_s':series[0].get('think_time',0),
             'replicate_p95_ms':[r['p95_ms'] for r in series],
             'replicate_rps':[r['rps'] for r in series],'files':[r['file'] for r in series]}
        for key in series[0]['resources']:
            values=[r['resources'][key] for r in series if r['resources'][key] is not None]
            row[key]=sum(values) if key.endswith('_delta') or key=='resource_samples' else max(values,default=None)
        summary.append(row)
        if phase in {'mixed','users','background-control','background-loaded'}:
            for subcase in sorted({s['case'] for s in samples}):
                subset=[s for s in good if s['case']==subcase]
                case_rows.append({'phase':phase,'variant':variant,'concurrency':c,'case':subcase,'requests':len(subset),
                                  'p50_ms':quantile([s['ms'] for s in subset],.5),
                                  'p95_ms':quantile([s['ms'] for s in subset],.95,20),
                                  'p99_ms':quantile([s['ms'] for s in subset],.99,300),
                                  'response_bytes_total':sum(s['bytes'] for s in subset)})
    output={'summary':summary,'mixed_by_case':case_rows,'source_files':[r['file'] for r in results],
            'method':'All percentiles use pooled successful request latencies. RPS is requests / summed measured duration. Sampled PG counter deltas omit the unsampled edges and include concurrent background activity.',
            'measured_requests':sum(r['requests'] for r in summary),'failed_requests':sum(r['requests']-r['statuses'].get('200',0) for r in summary)}
    (ROOT/'benchmark_results.json').write_text(json.dumps(output,indent=2)+'\n')
    keys=[k for k in summary[0] if k not in {'statuses','files','replicate_p95_ms','replicate_rps'}] if summary else []
    with (ROOT/'benchmark_results.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,lineterminator="\n");writer.writeheader()
        writer.writerows({k:r[k] for k in keys} for r in summary)
    with (ROOT/'mixed_by_case.csv').open('w',newline='') as stream:
        if case_rows:
            writer=csv.DictWriter(stream,fieldnames=list(case_rows[0]),lineterminator="\n");writer.writeheader();writer.writerows(case_rows)
    print(f'Aggregated {len(results)} series, {output["measured_requests"]} measured requests, {output["failed_requests"]} failures')


if __name__=='__main__':main()
