"""Standalone Matplotlib figures from fresh raw observations only."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parents[1]
CHARTS=OUT/'charts'
CHARTS.mkdir(exist_ok=True)
rows=json.loads((OUT/'benchmark_results.json').read_text())
colors={'rc2':'#717b8c','rc3':'#087f78','fix1':'#b26c16'}
plt.rcParams.update({'font.size':10,'figure.dpi':140,'axes.spines.top':False,'axes.spines.right':False})


def finish(name,title,ylabel):
    plt.title(title)
    plt.ylabel(ylabel)
    plt.grid(axis='y',alpha=.2)
    plt.tight_layout()
    plt.savefig(CHARTS/(name+'.png'))
    plt.savefig(CHARTS/(name+'.svg'))
    plt.close()


for field,name,title,label in [
    ('p95_ms','mixed-p95-vs-concurrency','Mixed p95; 3 paired repeats','seconds'),
    ('rps','rps-vs-concurrency','Mixed throughput; 3 paired repeats','requests / second'),
    ('pg_cpu_mean_pct','postgresql-cpu','PostgreSQL sampled CPU','% (100% = one core)'),
    ('app_cpu_mean_pct','worker-cpu','uWSGI container sampled CPU','% (100% = one core)'),
    ('worker_rss_peak_mib','worker-rss','Largest worker sampled RSS','MiB'),
    ('sql_wall_mean_ms','sql-wall-vs-concurrency','Client SQL execute wall / request','milliseconds')]:
    plt.figure(figsize=(7,4))
    for variant in ['rc2','rc3']:
        data=sorted((r for r in rows if r['phase']=='campaign' and r['variant']==variant),key=lambda r:r['concurrency'])
        scale=1000 if field=='p95_ms' else 1
        plt.plot([r['concurrency'] for r in data],[(r[field]/scale if r[field] is not None else float('nan')) for r in data],'o-',label=variant.upper(),color=colors[variant])
        if field in ['p95_ms','rps']:
            for row in data:
                ys=[run[field]/scale for run in row['runs']]
                plt.scatter([row['concurrency']]*len(ys),ys,s=12,color=colors[variant],alpha=.45)
    plt.xlabel('Concurrency')
    plt.xticks([1,5,10,15,25])
    plt.legend()
    finish(name,title,label)

cases=['dashboard','filtered_product','products','web_findings','web_test','web_products']
plt.figure(figsize=(8,4.5))
for offset,variant in [(-.18,'rc2'),(.18,'rc3')]:
    data={r['case']:r for r in rows if r['phase']=='endpoints' and r['variant']==variant}
    plt.bar([i+offset for i in range(len(cases))],[data[c]['p95_ms']/1000 for c in cases],width=.35,color=colors[variant],label=variant.upper())
plt.xticks(range(len(cases)),cases,rotation=20,ha='right')
plt.legend()
finish('slow-endpoint-p95','Dedicated endpoints, n=160 / variant','p95 seconds')

plt.figure(figsize=(7,4))
for variant in ['rc2','rc3']:
    data=[]
    for path in (OUT/'raw').glob(f'campaign-{variant}-*-c25-mixed.json'):
        data.extend(s['ms']/1000 for s in json.loads(path.read_text())['samples'])
    data.sort()
    plt.plot(data,[(i+1)/len(data) for i in range(len(data))],label=variant.upper(),color=colors[variant])
plt.xlabel('Response time, seconds')
plt.legend()
finish('response-time-distribution','Empirical CDF; 900 requests / variant at c25','Cumulative fraction')

plt.figure(figsize=(8,4))
for offset,variant in [(-.18,'fix1'),(.18,'rc3')]:
    data={r['case']:r for r in rows if r['phase']=='endpoints' and r['variant']==variant}
    plt.bar([i+offset for i in range(2)],[data[c]['p95_ms']/1000 for c in ['web_findings','web_test']],width=.35,color=colors[variant],label='Authorization only' if variant=='fix1' else 'Retained RC3')
plt.xticks([0,1],['Findings UI','Test UI'])
plt.legend()
finish('before-after-ui-fixes','Incremental UI fixes, n=160 per endpoint','p95 seconds')

fig,axes=plt.subplots(1,2,figsize=(8,4))
initial=[json.loads((OUT/'raw'/name).read_text()) for name in ['fix1-before-rc2-r1-c25-mixed.json','fix1-after-rc3-r1-c25-mixed.json']]
for ax,field,scale,label in [(axes[0],'p95_ms',1000,'Mixed p95, seconds'),(axes[1],'rps',1,'Requests / second')]:
    ax.bar(['RC2','Authorization only'],[r[field]/scale for r in initial],color=[colors['rc2'],colors['fix1']])
    ax.set_ylabel(label);ax.grid(axis='y',alpha=.2)
fig.suptitle('Initial authorization-only diagnostic pair; n=300/build, c25')
plt.tight_layout();plt.savefig(CHARTS/'before-after-authorization.png');plt.savefig(CHARTS/'before-after-authorization.svg');plt.close()

plt.figure(figsize=(7,4))
for variant in ['fix1','dashboard']:
    data=[json.loads(p.read_text()) for p in (OUT/'raw/rejected-dashboard').glob(f'incremental-{variant}-*-mixed.json')]
    data.sort(key=lambda r:r['repeat'])
    plt.plot([r['repeat'] for r in data],[r['p95_ms']/1000 for r in data],'o-',label='Authorization only' if variant=='fix1' else 'Rejected counter batching')
plt.xticks([1,2,3])
plt.xlabel('Paired repeat')
plt.legend()
finish('rejected-dashboard-batching','Rejected experiment: every paired p95 worsened','Mixed p95 seconds')

for variant in ['rc2','rc3']:
    data={}
    for sql in json.loads((OUT/'raw'/f'sql-final-{variant}.json').read_text()):
        if sql['case'] not in ['findings','filtered_product','finding_detail','products','tests','engagements','dashboard','web_products','endpoints']:continue
        key=sql['sql']
        entry=data.setdefault(key,{'ms':0,'calls':0,'cases':set()})
        entry['ms']+=sql['ms'];entry['calls']+=1;entry['cases'].add(sql['case'])
    top=sorted(data.values(),key=lambda r:r['ms'],reverse=True)[:10]
    plt.figure(figsize=(8,4.8))
    plt.barh(range(len(top)),[r['ms']/1000 for r in top],color=colors[variant])
    plt.yticks(range(len(top)),[','.join(sorted(r['cases']))+f" ({r['calls']} calls)" for r in top])
    plt.gca().invert_yaxis()
    plt.xlabel('Cumulative client SQL execute wall, seconds')
    finish('top-sql-'+variant,variant.upper()+' diagnostic SQL costs; not PostgreSQL CPU','')

fig,axes=plt.subplots(2,1,figsize=(8,6),sharex=True)
for variant in ['rc2','rc3']:
    paths=sorted((OUT/'raw').glob(f'campaign-{variant}-*-c25-mixed-metrics.jsonl'))
    offset=0
    for path in paths:
        samples=[json.loads(line) for line in path.read_text().splitlines() if line]
        if not samples:continue
        first=samples[0]['at'];xs=[s['at']-first+offset for s in samples]
        axes[0].plot(xs,[s.get('pg',{}).get('io_wait',0) for s in samples],color=colors[variant],label=variant.upper() if offset==0 else None)
        axes[1].plot(xs,[s.get('pg',{}).get('lock_wait',0) for s in samples],color=colors[variant])
        offset=xs[-1]+3
axes[0].set_title('PostgreSQL wait samples, consecutive c25 repeat windows')
axes[0].set_ylabel('IO wait backends')
axes[1].set_ylabel('Lock wait backends')
axes[1].set_xlabel('Seconds within concatenated windows; warmup included')
axes[0].legend()
plt.tight_layout();plt.savefig(CHARTS/'postgresql-waits.png');plt.savefig(CHARTS/'postgresql-waits.svg');plt.close()
print('Charts generated',len(list(CHARTS.glob('*.png'))))

for variant in ['rc2','rc3']:
    path=OUT/'raw'/f'pg-stat-statements-{variant}-c25.json'
    if not path.exists():continue
    data=[r for r in json.loads(path.read_text()) if 'pg_stat_statements' not in r['query']][:10]
    plt.figure(figsize=(8,4.8))
    plt.barh(range(len(data)),[r['total_exec_time']/1000 for r in data],color=colors[variant])
    plt.yticks(range(len(data)),[f"Q{i+1}: {r['calls']} calls" for i,r in enumerate(data)])
    plt.gca().invert_yaxis()
    plt.xlabel('Total PostgreSQL execution time, seconds')
    finish('server-top-sql-'+variant,variant.upper()+' server SQL on isolated copy; IDs in SQL_ANALYSIS','')
