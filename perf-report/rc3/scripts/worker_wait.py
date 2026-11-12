"""Read access logs after run completion; residual is queue+proxy/network, not pure queue."""
import datetime
import json
import re
import subprocess
import time
from lab import ROOT, OUT, PRIVATE, WEB, save

actors=json.loads((ROOT/'perf-report/final/actors.json').read_text())
users={a['username']:index for index,a in enumerate(actors) if a['username']}
scenarios=json.loads((ROOT/'perf-report/round5/scenarios.json').read_text())
credentials=json.loads((PRIVATE/'accounts.json').read_text())
pattern=re.compile(r'^([^ ]+) \[pid: (\d+)\|.*?\] .*? \(([^()]*)\) .*? GET (\S+) => generated (\d+) bytes in (\d+) msecs .*? (\d{3})\)')
seen=set()
while True:
    for path in sorted((OUT/'raw').glob('campaign-*-c25-mixed.json')):
        if path.name in seen:continue
        try:data=json.loads(path.read_text())
        except json.JSONDecodeError:continue
        if 'image_id' not in data:continue  # benchmark output precedes controller metadata
        try:actual=subprocess.check_output(['docker','inspect','--format','{{.Image}}',WEB],text=True,stderr=subprocess.DEVNULL).strip()
        except subprocess.CalledProcessError:continue  # container replacement between runs
        if actual!=data['image_id']:
            seen.add(path.name);continue
        result=subprocess.run(['docker','logs','--timestamps','--since',str(data['started_at']),'--until',str(data['ended_at']+1),WEB],capture_output=True,text=True,check=True)
        logs=result.stdout+result.stderr
        records=[]
        for line in logs.splitlines():
            match=pattern.search(line)
            if not match:continue
            timestamp,pid,user,url,size,ms,status=match.groups()
            at=datetime.datetime.fromisoformat(timestamp.replace('Z','+00:00')).timestamp()
            records.append(dict(at=at,pid=int(pid),actor=users.get(user,0 if user=='admin' else None),url=url,bytes=int(size),worker_ms=int(ms),status=status))
        matched=[]
        used=set()
        for sample in sorted(data['samples'],key=lambda x:x['at']+x['ms']/1000):
            url=scenarios[sample['case']]['url'].format(**credentials[sample['actor']],nonce='unused')
            candidates=[(abs(record['at']-(sample['at']+sample['ms']/1000)),index,record) for index,record in enumerate(records) if index not in used and record['actor']==sample['actor'] and record['url']==url and record['bytes']==sample['bytes'] and record['status']==sample['status']]
            if not candidates:continue
            distance,index,record=min(candidates,key=lambda x:x[0])
            if distance>.25:continue
            used.add(index)
            matched.append(dict(case=sample['case'],actor=sample['actor'],http_ms=sample['ms'],worker_ms=record['worker_ms'],queue_proxy_network_residual_ms=max(0,sample['ms']-record['worker_ms']),completion_match_error_ms=distance*1000,pid=record['pid']))
        save(OUT/'raw'/(path.stem+'-worker-wait.json'),dict(run=path.name,matched=len(matched),total=len(data['samples']),method='Nearest completion within 250 ms; identical actor, URL, bytes and status; residual includes proxy/network overhead',samples=matched))
        seen.add(path.name)
        print('Worker timing',path.name,len(matched),flush=True)
    if (OUT/'raw/campaign-complete.json').exists():break
    time.sleep(1)
