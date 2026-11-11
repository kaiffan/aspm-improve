#!/usr/bin/env python3
"""Render standalone PNG/SVG charts from the measured aggregate JSON."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parent
rows=json.loads((ROOT/'benchmark_results.json').read_text())['summary']
COLORS={'original':'#78879b','current':'#c17d24','final':'#00857d'}
NAMES={'original':'Original 3.5.100','current':'Current (R1–R3)','final':'Final (R4)'}
LABELS={'findings':'Findings · 100 rows','finding_detail':'Finding detail','filtered_product':'Findings · Product + severity','filtered_severity':'Findings · severity + active','offset':'Findings · offset 500,000','products':'Products · full list','product_detail':'Product · full detail','engagements':'Engagements list','tests':'Tests list','dashboard':'Dashboard','web_products':'Products UI','web_findings':'Findings UI','web_test':'Test UI','simple_metrics_cold':'Simple Metrics · fresh render'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'#f8fafc','axes.facecolor':'#f8fafc','grid.alpha':.22})
charts=ROOT/'charts';charts.mkdir(exist_ok=True)

def save(fig,name):
    fig.savefig(charts/(name+'.svg'),bbox_inches='tight')
    fig.savefig(charts/(name+'.png'),dpi=170,bbox_inches='tight')
    plt.close(fig)

end={(r['variant'],r['case']):r for r in rows if r['phase']=='endpoints' and r['concurrency']==1}
cases=[c for c in LABELS if ('original',c) in end and ('final',c) in end]
for metric,title,name,label in [('p95_ms','Original vs Final · endpoint p95','endpoint_p95','HTTP p95 · ms (log scale)'),('rps','Original vs Final · endpoint throughput','endpoint_rps','Requests / second (log scale)'),('sql_count_median','Original vs Final · SQL statements','sql_queries','Median statements per HTTP request')]:
    fig,ax=plt.subplots(figsize=(11,7))
    y=np.arange(len(cases))
    for variant,offset in [('original',-.19),('final',.19)]:
        values=[end[variant,c][metric] for c in cases]
        ax.barh(y+offset,values,height=.35,color=COLORS[variant],label=NAMES[variant])
    ax.set_yticks(y,[LABELS[c] for c in cases]);ax.invert_yaxis()
    if metric!='sql_count_median':ax.set_xscale('log')
    ax.set_xlabel(label);ax.set_title(title,pad=38);ax.grid(axis='x');ax.legend(loc='lower center',bbox_to_anchor=(.5,1.005),ncol=2,frameon=False)
    fig.text(.1,.01,'Same standard responses · 80 measured requests / variant / endpoint · concurrency 1',fontsize=9,color='#536075')
    fig.tight_layout(rect=(0,.03,1,1));save(fig,name)

mixed=[r for r in rows if r['phase']=='mixed']
for metric,title,name,label in [('p95_ms','Mixed workload · p95 vs concurrency','mixed_p95','Aggregate HTTP p95 · ms'),('rps','Mixed workload · throughput vs concurrency','mixed_rps','Aggregate requests / second')]:
    fig,ax=plt.subplots(figsize=(10,5))
    for variant in COLORS:
        selected=sorted([r for r in mixed if r['variant']==variant],key=lambda r:r['concurrency'])
        if selected:ax.plot([r['concurrency'] for r in selected],[r[metric] for r in selected],marker='o',linewidth=2.5,color=COLORS[variant],label=NAMES[variant])
    ax.set_xticks([1,5,10,15,25]);ax.set_xlabel('Concurrent requests · rotating pool of 25 identities');ax.set_ylabel(label);ax.set_title(title);ax.grid();ax.legend()
    fig.text(.1,.01,'Fixed mix includes full Product responses and Dashboard · p95 pooled from request samples',fontsize=9,color='#536075')
    fig.tight_layout(rect=(0,.03,1,1));save(fig,name)

fig,axes=plt.subplots(2,2,figsize=(12,8))
for ax,key,title in zip(axes.flat,['uwsgi_cpu_peak','pg_cpu_peak','uwsgi_worker_rss_mib_peak','pg_container_mib_peak'],['uWSGI CPU · sampled peak, %','PostgreSQL CPU · sampled peak, %','uWSGI worker RSS · sampled peak, MiB','PostgreSQL container memory · sampled peak, MiB']):
    for variant in COLORS:
        selected=sorted([r for r in mixed if r['variant']==variant and r.get(key) is not None],key=lambda r:r['concurrency'])
        if selected:ax.plot([r['concurrency'] for r in selected],[r[key] for r in selected],marker='o',color=COLORS[variant],label=NAMES[variant])
    ax.set_title(title,fontsize=11);ax.set_xticks([1,5,10,15,25]);ax.set_xlabel('Concurrent requests');ax.grid()
axes[0,0].legend(fontsize=9)
fig.suptitle('Mixed workload · observed resource peaks',fontsize=15,weight='bold')
fig.text(.1,.01,'CPU 100% = one logical core · RSS is per worker; PG container memory is not a process RSS sum',fontsize=9,color='#536075')
fig.tight_layout(rect=(0,.03,1,.96));save(fig,'resources')
print('Rendered six charts as PNG and SVG')
