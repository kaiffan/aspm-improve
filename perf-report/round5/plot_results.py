"""Static plots rebuilt from raw-backed benchmark_results.json; no smoothing."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

R=Path(__file__).resolve().parent;rows=json.loads((R/'benchmark_results.json').read_text())
V=['original','round4','round5'];names=['Original 3.5.100','Final Round 4','Final Round 5'];colors=['#b65050','#bd8b30','#197568']
D={(r['variant'],r['phase'],r['concurrency'],r['case']):r for r in rows}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
def save(fig,name):
 fig.tight_layout();fig.savefig(R/'charts'/f'{name}.png',bbox_inches='tight');plt.close(fig)
def bars(cases,phase,c,field,label,title,name):
 fig,ax=plt.subplots(figsize=(max(9,len(cases)*1.1),5));x=np.arange(len(cases));width=.25
 for i,v in enumerate(V):
  rs=[D[(v,phase,c,k)] for k in cases];val=[r[field]/(1000 if field.endswith('_ms') else 1) for r in rs]
  ax.bar(x+(i-1)*width,val,width,color=colors[i],label=names[i])
  for j,r in enumerate(rs):
   if field=='p95_ms':
    ys=[a['p95_ms']/1000 for a in r['runs']];ax.scatter([x[j]+(i-1)*width]*len(ys),ys,s=18,c='black',zorder=3,marker='_')
  for xx,y,r in zip(x+(i-1)*width,val,rs):ax.text(xx,y,f'{y:.2g}\nn={r["n"]}',ha='center',va='bottom',fontsize=7)
 ax.set_xticks(x,cases,rotation=25,ha='right');ax.set_ylabel(label);ax.set_title(title);ax.legend(fontsize=8);ax.grid(axis='y',alpha=.15)
 save(fig,name)
critical=[r['case'] for r in rows if r['variant']=='original' and r['phase']=='endpoints' and r['concurrency']==1 and r['case']!='ALL' and (r['p95_ms'] or 0)>500]
if critical:
 bars(critical,'endpoints',1,'p95_ms','HTTP p95, seconds','Standalone c=1: Original p95 > 500 ms; black ticks = repeat p95','critical_endpoints')
 fig,ax=plt.subplots(figsize=(9,4.8));x=np.arange(len(critical))
 for i,v in enumerate(V[1:]):
  ys=[D[('original','endpoints',1,k)]['p95_ms']/D[(v,'endpoints',1,k)]['p95_ms'] for k in critical];ax.bar(x+(i-.5)*.35,ys,.35,label=names[i+1],color=colors[i+1])
 ax.axhline(1,color='black',linewidth=.8);ax.set_xticks(x,critical,rotation=25,ha='right');ax.set_ylabel('Original p95 / candidate p95 (×)');ax.legend();ax.set_title('Measured speedup: same standard responses, n=80/case, two repeats');save(fig,'speedup_factors')
 for field,label,name in [('rps','Requests / second','critical_rps'),('sql_count_median','Median SQL statements / request','critical_sql')]:bars(critical,'endpoints',1,field,label,'Critical endpoints, identical scenarios',name)
levels=[1,5,10,15,25]
fig,axs=plt.subplots(1,3,figsize=(13,4.4))
for v,label,col in zip(V,names,colors):
 for ax,field,scale in zip(axs,['p95_ms','rps','pg_cpu_mean'],[1000,1,100]):
  rs=[D[(v,'mixed',c,'ALL')] for c in levels];ax.plot(levels,[r[field]/scale for r in rs],'-o',label=label,color=col)
  if field=='p95_ms':
   for c,r in zip(levels,rs):ax.scatter([c]*len(r['runs']),[a['p95_ms']/1000 for a in r['runs']],color=col,marker='x',s=24)
  elif field in ['rps','pg_cpu_mean']:
   for c,r in zip(levels,rs):
    vals=[a[field]/scale for a in r['runs'] if a.get(field) is not None];ax.scatter([c]*len(vals),vals,color=col,marker='x',s=24)
  ax.set_xlabel('Concurrent in-flight requests');ax.grid(alpha=.2);ax.set_xticks(levels)
for ax,label in zip(axs,['HTTP p95, seconds','Requests / second','PostgreSQL CPU, logical cores']):ax.set_ylabel(label)
axs[0].legend(fontsize=8);fig.suptitle('Unchanged mix: n=200 at c1, n=600 at c5–25; two repeats, no smoothing');save(fig,'saturation_curves')
cases=[k[3] for k in D if k[0]=='original' and k[1]=='mixed' and k[2]==25 and k[3]!='ALL']
fig,axs=plt.subplots(1,2,figsize=(13,5))
for v,label,col in zip(V,names,colors):
 rs=[D[(v,'mixed',25,k)] for k in cases];ys=[r['p95_ms']/1000 if r['p95_ms'] else np.nan for r in rs];axs[0].plot(cases,ys,'o',label=label,color=col)
axs[0].set_ylabel('HTTP p95, seconds (n ≥ 20)');axs[0].tick_params(axis='x',rotation=65);axs[0].legend(fontsize=8)
bottom=np.zeros(3)
for k in cases:
 values=[100*D[(v,'mixed',25,k)]['latency_ms_sum']/D[(v,'mixed',25,'ALL')]['latency_ms_sum'] for v in V]
 axs[1].bar(names,values,bottom=bottom,label=k);bottom+=values
axs[1].set_ylabel('Share of sum(request elapsed time), %');axs[1].legend(fontsize=7,bbox_to_anchor=(1,1));axs[1].tick_params(axis='x',rotation=15)
fig.suptitle('c=25: request latency contribution; includes queuing, not CPU attribution');save(fig,'latency_contribution')
bars(['products','dashboard','web_products','ALL'],'mixed',25,'p95_ms','HTTP p95, seconds','Original → Round 4 → Round 5: same mix, two repeats; black ticks = repeat p95','round5_before_after')
fig,axs=plt.subplots(1,2,figsize=(10,4))
for v,label,col in zip(V,names,colors):
    rs=[D[(v,'mixed',c,'ALL')] for c in levels]
    axs[0].plot(levels,[r['web_container_memory_peak_mib'] for r in rs],'-o',color=col,label=label)
    axs[1].plot(levels,[r['web_cpu_mean']/100 for r in rs],'-o',color=col,label=label)
for ax in axs:ax.set_xticks(levels);ax.set_xlabel('Concurrent in-flight requests');ax.grid(alpha=.2)
axs[0].set_ylabel('Django/uWSGI container working set peak, MiB');axs[1].set_ylabel('uWSGI CPU, logical cores');axs[0].legend(fontsize=8)
fig.suptitle('Measured process resources; no smoothing');save(fig,'application_resources')
fig,ax=plt.subplots(figsize=(10,5));x=np.arange(len(cases))
for i,v in enumerate(V[1:]):
    ys=[D[('original','mixed',25,k)]['p95_ms']/D[(v,'mixed',25,k)]['p95_ms'] for k in cases]
    ax.bar(x+(i-.5)*.35,ys,.35,label=names[i+1],color=colors[i+1])
    for xx,y in zip(x+(i-.5)*.35,ys):ax.text(xx,y,f'{y:.1f}×',ha='center',va='bottom',fontsize=8)
ax.axhline(1,color='black',linewidth=.8);ax.set_xticks(x,[f'{k}\nn={D[("round5","mixed",25,k)]["n"]}' for k in cases],rotation=35,ha='right');ax.set_ylabel('Original p95 / candidate p95');ax.legend();ax.set_title('Every scenario in the same c25 mix: measured speedup');save(fig,'mixed_speedup_factors')
raw={v:[] for v in V}
for path in (R/'raw').glob('mixed-r*-c25-mixed.json'):
    d=json.loads(path.read_text());raw[d['variant']]+=d['samples']
fig,ax=plt.subplots(figsize=(13,6));x=np.arange(len(cases))
for i,v in enumerate(V):
    data=[[s['ms'] for s in raw[v] if s['case']==k] for k in cases]
    boxes=ax.boxplot(data,positions=x+(i-1)*.24,widths=.20,whis=(5,95),showfliers=True,patch_artist=True,manage_ticks=False,medianprops={'color':'black'},flierprops={'markersize':2,'alpha':.6})
    for patch in boxes['boxes']:patch.set_facecolor(colors[i]);patch.set_alpha(.7)
    ax.plot([],[],color=colors[i],label=names[i])
ax.set_yscale('log');ax.set_xticks(x,[f'{k}\nn={len([s for s in raw["round5"] if s["case"]==k])}' for k in cases],rotation=35,ha='right');ax.set_ylabel('HTTP latency, ms (log scale)');ax.set_title('c25 latency distributions: median/IQR, 5–95% whiskers, all outliers retained');ax.legend();ax.grid(axis='y',alpha=.2);save(fig,'latency_distribution')
