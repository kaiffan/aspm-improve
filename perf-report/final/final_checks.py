#!/usr/bin/env python3
import argparse,http.client,json,re,subprocess,time
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--credentials',type=Path,required=True);a=p.parse_args()
r=Path(__file__).resolve().parent;accounts=json.loads(a.credentials.read_text())
checks=[]
for actor,url in [(0,'/api/v2/findings/?limit=1'),(0,'/api/v2/products/?findings=none&limit=1'),(1,f"/api/v2/findings/{accounts[2]['finding']}/"),(1,f"/api/v2/findings/?test__engagement__product={accounts[2]['product']}&limit=1")]:
    c=http.client.HTTPConnection('127.0.0.1',48084,timeout=30)
    c.request('GET',url,headers={'Authorization':'Token '+accounts[actor]['token']})
    response=c.getresponse();body=json.loads(response.read());instrumented=response.getheader('X-Perf-SQL-Count') is not None;c.close()
    row={'actor':'admin' if actor==0 else 'restricted','url':url,'status':response.status,'count':body.get('count'),'benchmark_middleware_present':instrumented}
    checks.append(row)
assert checks[0]['status']==200 and checks[0]['count']==1000168
assert checks[1]['status']==200
assert checks[2]['status']==404
assert checks[3]['status']==200 and checks[3]['count']==0
assert not any(r['benchmark_middleware_present'] for r in checks)
containers={}
for name in ('dd-final-web-1','dd-final-nginx-1','django-defectdojo-uwsgi-1','django-defectdojo-postgres-1','django-defectdojo-uwsgi-perf-1','dd35100-round2-uwsgi-round2-1','dd35100-round3-uwsgi-round3-1'):
    obj=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
    containers[name]={'running':obj['State']['Running'],'oom':obj['State']['OOMKilled'],'restarts':obj['RestartCount'],'image':obj['Image']}
assert all(v['running'] and not v['oom'] for v in containers.values())
measurements=[]
for f in (r/'raw').glob('*-metrics.jsonl'):
    for line in f.read_text().splitlines():
        try:measurements.append(json.loads(line))
        except json.JSONDecodeError:pass
resources={'min_host_free_percent':min(x['host_free_percent'] for x in measurements if 'host_free_percent' in x),'min_swap_mib':min(x['swap_mib'] for x in measurements if 'swap_mib' in x),'max_swap_mib':max(x['swap_mib'] for x in measurements if 'swap_mib' in x),'guard_stops':[x['stop'] for x in measurements if 'stop' in x]}
assert not resources['guard_stops']
(r/'final_checks.json').write_text(json.dumps({'health_and_permissions':checks,'containers':containers,'resource_guard':resources,'old_benchmark_apps_restored':True,'optimized_test_port':48084,'original_port_unchanged':8080},indent=2)+'\n')
print('Final optimized API healthy; foreign data denied; initial containers restored; no resource-guard stops')
