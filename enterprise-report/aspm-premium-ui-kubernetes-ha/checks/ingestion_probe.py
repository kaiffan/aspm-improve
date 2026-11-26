"""Run via the temporary observer inside the synthetic ASPM lab."""
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

api = 'http://aspm-aspm/api/aspm/v1'
headers = {'Authorization':'ASPM '+fixture['token'],'Host':'127.0.0.1','Connection':'close'}
mode = sys.argv[1]

def submit(index):
    content = json.dumps({'findings':[{'title':f'ASPM HA synthetic {index}','description':'Local recovery fixture','severity':'High'}]}).encode()
    data = {'project_id':fixture['product_id'],'repository_id':fixture['repository_id'],'commit_sha':(fixture['suffix']+str(index)).ljust(40,'a'),'scanner_type':'Generic Findings Import','idempotency_key':fixture['suffix']+'-'+str(index),'pipeline_id':'ha-recovery'}
    started = time.monotonic()
    response = requests.post(api+'/scans/',headers=headers,data=data,files={'file':('scan.json',content,'application/json')},timeout=10)
    assert response.status_code in (200,202),f'scan HTTP {response.status_code}'
    return {'scan':response.json()['id'],'status':response.status_code,'started':time.time(),'ms':round((time.monotonic()-started)*1000,2),'sha256':hashlib.sha256(content).hexdigest()}

def get(path, base=api):
    response = requests.get(base+path,headers=headers,timeout=10)
    assert response.status_code==200,f'{path}: HTTP {response.status_code}'
    return response

if mode=='submit':
    with ThreadPoolExecutor(max_workers=3) as pool:
        print(json.dumps(list(pool.map(submit,range(3)))),flush=True)
elif mode=='finish':
    deadline = time.monotonic()+130
    states = {}
    while time.monotonic()<deadline:
        for row in scans:
            if states.get(row['scan'],{}).get('status') != 'COMPLETED':
                state=get('/scans/'+row['scan']+'/').json()
                assert state['status']!='FAILED',state['error_code']
                states[row['scan']]=state
        if all(state['status']=='COMPLETED' for state in states.values()):
            break
        time.sleep(1.4)
    assert all(state['status']=='COMPLETED' and state['finding_count']==1 and state['test'] for state in states.values()), 'Missing or duplicated completed findings'
    assert len({state['test'] for state in states.values()}) == len(scans)
    result=[]
    for index,row in enumerate(scans):
        replay=submit(index)
        assert (replay['status'],replay['scan']) == (200,row['scan'])
        stored=get('/scans/'+row['scan']+'/artifact/')
        assert hashlib.sha256(stored.content).hexdigest()==row['sha256']
        state=states[row['scan']]
        result.append({'scan':row['scan'],'commit':state['commit'],'test':state['test'],'attempt':state['attempt'],'observed_findings':state['finding_count'],'acceptance_ms':row['ms'],'replay':replay['status'],'artifact_sha256':row['sha256'],'timings':state['timings'],'finished_at':state['finished_at']})
    selected=result[0]
    response=requests.post(api+f'/commits/{selected["commit"]}/reports/',headers=headers,json={'scan_ids':[selected['scan']]},timeout=10)
    assert response.status_code==202,f'report submission {response.status_code}'
    report=response.json()['id']
    for _ in range(45):
        reports=get(f'/commits/{selected["commit"]}/reports/').json()
        status=next(x for x in reports if x['id']==report)['status']
        assert status!='FAILED'
        if status=='COMPLETED': break
        time.sleep(1)
    assert status=='COMPLETED'
    download=get(f'/reports/{report}/download/?format=json')
    result={'scans':result,'report':{'id':report,'sha256':hashlib.sha256(download.content).hexdigest()},'zero_finalize':True}
    print(json.dumps(result,indent=2))
elif mode=='storage':
    scan=result['scans'][0]
    paths={f'/scans/{scan["scan"]}/artifact/':scan['artifact_sha256'],f'/reports/{result["report"]["id"]}/download/?format=json':result['report']['sha256']}
    records=[]
    for address in sys.argv[2:]:
        for path,expected in paths.items():
            response=get(path, 'http://'+address+':8080/api/aspm/v1')
            digest=hashlib.sha256(response.content).hexdigest()
            assert digest==expected, 'Evidence checksum mismatch'
            assert 'no-store' in response.headers['Cache-Control']
            records.append({'pod_ip':address,'path':path,'sha256':digest,'bytes':len(response.content)})
    print(json.dumps(records,indent=2))
