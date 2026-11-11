"""Figures from measured JSON only. Run markers show repeat variation; no smoothing."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=Path(__file__).resolve().parents[1];rows=json.loads((R/'benchmark_results.json').read_text());D={(x['variant'],x['phase'],x['concurrency'],x['case']):x for x in rows}
colors={'original':'#8c929a','round5':'#9e6fc3','ui':'#c1ff05','rc':'#ff7d32'};names={'original':'Original 3.5.100','round5':'Round 5','ui':'UI stage (paired A/B)','rc':'Final RC image (follow-up)'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':145})
def save(fig,name):fig.tight_layout();fig.savefig(R/'charts'/(name+'.png'),bbox_inches='tight');plt.close(fig)
for key,ylabel,scale in [('p95_ms','Pooled p95, seconds',1000),('rps','Throughput, requests/s',1),('pg_cpu_mean_pct','PostgreSQL mean CPU, % (100% = one core)',1)]:
 fig,ax=plt.subplots(figsize=(8,4.8))
 for v in ['round5','ui']:
  xs=sorted(x['concurrency'] for x in rows if x['variant']==v and x['phase']=='mixed' and x['case']=='mixed')
  rs=[D[v,'mixed',c,'mixed'] for c in xs];ys=[x[key]/scale if x[key] is not None else np.nan for x in rs]
  ax.plot(xs,ys,marker='o',color=colors[v],markeredgecolor='#202327',linewidth=2,label=names[v])
  if key in ('p95_ms','rps'):
   for c,r in zip(xs,rs):ax.scatter([c]*len(r['runs']),[x[key]/scale for x in r['runs']],color='#202327',marker='_',s=45,zorder=5)
 ax.set_xticks([1,5,10,15,25]);ax.set_xlabel('Simultaneous requests; 25-identity pool, no think time');ax.set_ylabel(ylabel);ax.set_title('Same-copy mixed workload; two repetitions per point');ax.legend();ax.grid(alpha=.18);save(fig,'mixed-'+key)
cs=['dashboard','web_findings','web_test','web_products','findings','products','tests']
fig,ax=plt.subplots(figsize=(11,4.8));x=np.arange(len(cs))
for i,v in enumerate(['round5','ui']):
 rs=[D[v,'endpoints',1,k] for k in cs];ys=[r['p95_ms']/1000 for r in rs];pos=x+(i-.5)*.36
 ax.bar(pos,ys,.36,color=colors[v],edgecolor='#555',label=names[v])
 for p,y,r in zip(pos,ys,rs):ax.text(p,y,f'{y:.2f}\nn={r["n"]}',ha='center',va='bottom',fontsize=7)
 for p,r in zip(pos,rs):ax.scatter([p]*len(r['runs']),[a['p95_ms']/1000 for a in r['runs']],c='#202327',marker='_',s=35)
ax.set_xticks(x,cs,rotation=20,ha='right');ax.set_ylabel('HTTP p95, seconds');ax.set_title('Endpoint c=1, same data/settings; black marks = repeat p95');ax.legend();save(fig,'endpoint-p95')
comparison_phase='final' if ('rc','final',25,'mixed') in D else 'mixed'
final='rc' if ('rc',comparison_phase,25,'mixed') in D else 'ui'
vs=[v for v in ['original','round5',final] if (v,comparison_phase,25,'mixed') in D]
if len(vs)==3:
 fig,axes=plt.subplots(1,2,figsize=(10,4.7))
 for ax,key,label,scale in zip(axes,['p95_ms','rps'],['Pooled p95, seconds','Throughput, requests/s'],[1000,1]):
  rs=[D[v,comparison_phase,25,'mixed'] for v in vs];ys=[r[key]/scale for r in rs]
  ax.bar(range(3),ys,color=[colors[v] for v in vs],edgecolor='#555')
  ceiling=max([*ys,*[a[key]/scale for r in rs for a in r['runs']]])
  ax.set_ylim(0,ceiling*1.2)
  for j,r in enumerate(rs):
   repeats=[a[key]/scale for a in r['runs']];ax.scatter([j]*len(repeats),repeats,c='#202327',marker='_',s=45);ax.text(j,max(ys[j],*repeats)+ceiling*.025,f'{ys[j]:.2f}\nn={r["n"]}',ha='center',va='bottom')
  ax.set_xticks(range(3),['Original','Round 5','RC1']);ax.set_ylabel(label)
 fig.suptitle('Final counterbalanced c=25 comparison; exact release image; n=600 each');save(fig,'original-round5-rc1')
fig,ax=plt.subplots(figsize=(9,4.8));r=D.get(('rc','final',25,'mixed'),D.get(('ui','mixed',25,'mixed')))
if r:
 cs=list(r['by_case']);ys=[r['by_case'][c]['latency_sum_ms']/1000 for c in cs];ax.barh(cs,ys,color='#9e6fc3');ax.set_xlabel('Sum of request latency, seconds (overlaps under concurrency)');ax.set_title('RC1 workload latency contribution; not PostgreSQL execution time');save(fig,'latency-contribution')
print('Charts regenerated')

cs=['dashboard','web_findings','web_test','web_products','findings','products','tests']
fig,axes=plt.subplots(1,2,figsize=(11,4.8))
for ax,key,label in zip(axes,['median_sql_count','mean_bytes'],['Median SQL queries per request','Mean uncompressed response bytes']):
 for i,v in enumerate(['round5','ui']):
  vals=[D[v,'endpoints',1,k][key] for k in cs if (v,'endpoints',1,k) in D]
  if len(vals)==7:ax.bar(np.arange(7)+(i-.5)*.36,vals,.36,color=colors[v],edgecolor='#555',label=names[v])
 ax.set_xticks(np.arange(7),['dashboard','findings UI','test UI','products UI','findings API','products API','tests API'],rotation=35,ha='right');ax.set_ylabel(label);ax.legend(fontsize=8)
save(fig,'sql-and-response-size')
fig,ax=plt.subplots(figsize=(8,4.6))
for v in ['round5','ui']:
 xs=sorted(x['concurrency'] for x in rows if x['variant']==v and x['phase']=='mixed' and x['case']=='mixed');ax.plot(xs,[D[v,'mixed',c,'mixed']['worker_rss_peak_mib'] for c in xs],marker='o',color=colors[v],markeredgecolor='#202327',label=names[v])
ax.set_xlabel('Simultaneous requests');ax.set_ylabel('Peak RSS of one uWSGI worker, MiB');ax.set_title('All four workers sampled by /proc Name; RSS includes shared pages');ax.legend();ax.grid(alpha=.18);save(fig,'worker-rss')
if all((v,'final',25,'mixed') in D for v in ['original','round5','rc']):
 before=D['original','final',25,'mixed']['by_case'];after=D['rc','final',25,'mixed']['by_case'];cases=[k for k in before if before[k]['p95_ms'] and before[k]['p95_ms']>500];factors=[before[k]['p95_ms']/after[k]['p95_ms'] for k in cases]
 fig,ax=plt.subplots(figsize=(10,5.4));ax.barh(cases,factors,color=['#ff7d32' if x<1 else '#9e6fc3' for x in factors]);ax.axvline(1,color='#202327',linestyle='--',label='1 = no change')
 for i,(k,x) in enumerate(zip(cases,factors)):ax.text(x+.05,i,f'{x:.2f}x, n={after[k]["n"]}',va='center',fontsize=8)
 ax.set_xlim(0,max(factors)*1.2);ax.set_xlabel('Original p95 / final RC p95; below 1 means slower');ax.set_title('Critical scenarios in the same closed-loop mixed workload');ax.legend();save(fig,'critical-speedup')
