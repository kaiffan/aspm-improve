"""Compare complete JSON hashes and existing HTML context semantics, not HTML styling."""
import argparse
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--after',default='ui');p.add_argument('--output',default='compatibility.json');args=p.parse_args()
R=Path(__file__).resolve().parents[1]/'measurements'
left=json.loads((R/'profile-round5.json').read_text());right={(x['actor'],x['case']):x for x in json.loads((R/('profile-'+args.after+'.json')).read_text())}
rows=[]
for x in left:
 y=right[(x['actor'],x['case'])]
 item={k:x[k] for k in ('actor','case')}
 item.update(status=x['status'],status_equal=x['status']==y['status'])
 if 'payload_hash' in x:
  item.update(json_equal=x['payload_hash']==y['payload_hash'],count_equal=x.get('count')==y.get('count'),order_equal=x.get('ids')==y.get('ids'),bytes_equal=x['bytes']==y['bytes'])
 elif x['case'] in {'simple_metrics','simple_metrics_cold'}:
  item['rendered_metrics_equal']=x['metrics_cells']==y['metrics_cells']
  if x['case']=='simple_metrics_cold':item['context_equal']=x.get('semantic')==y.get('semantic')
  item['comparison']='Complete numeric table cells; full-page cache can bypass template signals'
 else:item['context_equal']=x.get('semantic')==y.get('semantic')
 rows.append(item)
failures=[x for x in rows if not all(v for k,v in x.items() if k.endswith('_equal'))]
(R/args.output).write_text(json.dumps({'pairs':len(rows),'failures':failures,'rows':rows},indent=2)+'\n')
print('Compared',len(rows),'pairs; failures:',len(failures))
if failures:raise SystemExit(1)
