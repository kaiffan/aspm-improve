#!/usr/bin/env python3
"""Compare saved complete JSON hashes and server-rendered context values."""
import json
from pathlib import Path

root=Path(__file__).resolve().parent
profiles={v:{(r['actor'],r['case']):r for r in json.loads((root/f'profile_{v}.json').read_text())} for v in ('original','current','final')}
rows=[]
for before in ('original','current'):
    for key,left in profiles[before].items():
        right=profiles['final'][key]
        row={'before':before,'actor':key[0],'case':key[1],'status_equal':left['status']==right['status'],'status':right['status']}
        if 'payload_hash' in left:
            row['json_equal']=left['payload_hash']==right['payload_hash']
            row['count_equal']=left.get('count')==right.get('count')
            row['order_equal']=left.get('ids')==right.get('ids')
            row['bytes_equal']=left['bytes']==right['bytes']
        else:
            row['context_equal']=left.get('semantic')==right.get('semantic')
            row['html_equal_without_csrf']=left.get('html_hash_without_csrf')==right.get('html_hash_without_csrf')
        rows.append(row)
(root/'compatibility.json').write_text(json.dumps(rows,indent=2)+'\n')
failures=[r for r in rows if not r['status_equal'] or not r.get('json_equal',True) or not r.get('context_equal',True)]
print(f'Compared {len(rows)} responses; semantic/JSON failures {len(failures)}; HTML hashes differing after CSRF removal {sum(not r.get("html_equal_without_csrf",True) for r in rows)}')
for r in failures:print({k:v for k,v in r.items() if k in ('before','actor','case','status')})
if failures:raise SystemExit(1)
