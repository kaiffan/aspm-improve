"""Generate charts directly from measured runs; dots/ranges are real repetitions."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

R=Path(__file__).resolve().parents[1]
rows=json.loads((R/'benchmark_results.json').read_text())
colors={'round5':'#72797D','rc1':'#8664A2','rc2':'#4F990D'}
names={'round5':'Round 5','rc1':'RC1','rc2':'RC2'}
labels={'dashboard':'Dashboard','web_findings':'Findings UI','web_test':'Test UI','web_products':'Products UI','findings':'Findings API','filtered_product':'Filtered Findings','finding_detail':'Finding detail','products':'Products full API','tests':'Tests API','engagements':'Engagements API'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})


def finish(fig,name):
    fig.tight_layout()
    fig.savefig(R/'charts'/name,bbox_inches='tight')
    plt.close(fig)


for key,title,ylabel,scale,filename in [
    ('p95_ms','Mixed latency: 3 repetitions × 300 requests / point','HTTP p95, seconds',.001,'p95-vs-concurrency.png'),
    ('rps','Mixed throughput: identical schedule and 25-account pool','Requests / second',1,'rps-vs-concurrency.png'),
    ('pg_cpu_mean_pct','PostgreSQL CPU: sampled during measured requests','CPU (%; 100% = one logical core)',1,'postgresql-cpu.png'),
    ('worker_rss_peak_mib','Peak RSS of one uWSGI worker (not physical app memory)','MiB',1,'worker-rss.png')]:
    fig,ax=plt.subplots(figsize=(9,5))
    for variant in colors:
        xs=sorted([r for r in rows if r['phase']=='mixed' and r['variant']==variant],key=lambda x:x['concurrency'])
        ax.plot([r['concurrency'] for r in xs],[r[key]*scale if r[key] is not None else np.nan for r in xs],marker='o',color=colors[variant],label=names[variant])
        if key in ['p95_ms','rps','pg_cpu_mean_pct','worker_rss_peak_mib']:
            for r in xs:
                values=[t[key]*scale for t in r['runs'] if t.get(key) is not None]
                if not values:continue
                ax.vlines(r['concurrency'],min(values),max(values),color=colors[variant],alpha=.6)
                ax.scatter([r['concurrency']]*len(values),values,s=18,color=colors[variant],alpha=.55)
    ax.set(xticks=[1,5,10,15,25],xlabel='Concurrent requests (zero think time)',ylabel=ylabel,title=title)
    ax.grid(axis='y',alpha=.2);ax.legend();finish(fig,filename)

endpoints={v:{r['case']:r for r in rows if r['phase']=='endpoints' and r['variant']==v} for v in colors}
critical=[case for case,row in endpoints['round5'].items() if row['p95_ms']>500]
for cases,title,filename in [(critical,'Critical endpoints: baseline p95 > 500 ms; n=120 per build','critical-endpoints.png'),(list(labels),'Before / after hardening: c=1, 2 × 60 observations per build','before-after-endpoints.png')]:
    fig,ax=plt.subplots(figsize=(11,6))
    positions=np.arange(len(cases));width=.25
    for offset,variant in enumerate(colors):
        points=[endpoints[variant][case]['p95_ms']/1000 for case in cases]
        ax.bar(positions+(offset-1)*width,points,width,color=colors[variant],label=names[variant])
        for index,case in enumerate(cases):
            values=[t['p95_ms']/1000 for t in endpoints[variant][case]['runs']]
            ax.vlines(positions[index]+(offset-1)*width,min(values),max(values),color='#242424',linewidth=1)
            ax.scatter([positions[index]+(offset-1)*width]*len(values),values,color='#242424',s=7)
    ax.set(xticks=positions,xticklabels=[labels[x] for x in cases],ylabel='HTTP p95, seconds',title=title)
    ax.tick_params(axis='x',labelrotation=30);ax.grid(axis='y',alpha=.2);ax.legend();finish(fig,filename)

for key,title,ylabel,filename in [
    ('mean_sql_ms','SQL execute time per request: includes DB waiting; c=1','Mean client-side SQL execute time, ms','sql-time.png'),
    ('median_sql_count','SQL queries per request; standard full responses','Median SQL query count','sql-count.png')]:
    cases=list(labels);positions=np.arange(len(cases));fig,ax=plt.subplots(figsize=(11,6))
    for offset,variant in enumerate(colors):
        ax.bar(positions+(offset-1)*.25,[endpoints[variant][case][key] for case in cases],.25,color=colors[variant],label=names[variant])
        for index,case in enumerate(cases):
            values=[run[key] for run in endpoints[variant][case]['runs']]
            ax.vlines(positions[index]+(offset-1)*.25,min(values),max(values),color='#242424',linewidth=1)
    ax.set(xticks=positions,xticklabels=[labels[x] for x in cases],ylabel=ylabel,title=title)
    ax.tick_params(axis='x',labelrotation=30);ax.grid(axis='y',alpha=.2);ax.legend();finish(fig,filename)
print('Generated 8 measured-data charts; no smoothing or historical-series pooling')
