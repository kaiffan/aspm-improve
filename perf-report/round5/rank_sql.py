"""Aggregate driver timings by redacted SQL shape. No query bindings are read."""
import argparse
import json
import math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
groups={};requests=0
for line in a.input.read_text().splitlines():
    requests+=1
    for q in json.loads(line)['queries']:
        g=groups.setdefault(q['id'],{'id':q['id'],'sql':q['sql'],'durations':[],'rows':0})
        g['durations'].append(q['ms']);g['rows']+=max(0,q['rows'])
rows=[]
for g in groups.values():
    ms=sorted(g.pop('durations'));g.update(calls=len(ms),total_ms=sum(ms),mean_ms=sum(ms)/len(ms),p95_ms=ms[math.ceil(len(ms)*.95)-1] if len(ms)>=20 else None)
    rows.append(g)
rows.sort(key=lambda g:g['total_ms'],reverse=True)
a.output.write_text(json.dumps({'request_count_including_warmup':requests,'timing':'driver wall time, not server-only execution time','queries':rows},indent=2)+'\n')
