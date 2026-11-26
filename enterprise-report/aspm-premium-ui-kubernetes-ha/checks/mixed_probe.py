"""Exercise HTTP concurrency against the isolated ASPM lab using disposable data."""
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date

service = 'http://aspm-aspm'
host = {'Host':'127.0.0.1','Connection':'close'}
admin=fixture['admin']
authentication=requests.post(service+'/api/v2/api-token-auth/',headers=host,json=admin,timeout=8)
assert authentication.status_code==200, f'Classic API token: HTTP {authentication.status_code}'
classic_headers={**host,'Authorization':'Token '+authentication.json()['token']}
date_string=date.today().isoformat()

def verify(response, code):
    assert response.status_code == code, f'{response.request.method} {response.request.path_url}: HTTP {response.status_code}, expected {code}'
    return response.json()

engagement=verify(requests.post(service+'/api/v2/engagements/',headers=classic_headers,json={'name':'HA Classic assessment','product':fixture['product_id'],'target_start':date_string,'target_end':date_string},timeout=10),201)
payload=json.dumps({'findings':[{'title':'Classic live contention fixture','description':'Synthetic Classic scanner finding','severity':'High'}]}).encode()
file={'file':('classic.json',payload,'application/json')}
scanner='Generic Findings Import'
initial=verify(requests.post(service+'/api/v2/import-scan/',headers=classic_headers,data={'engagement':engagement['id'],'scan_type':scanner,'deduplication_execution_mode':'sync'},files=file,timeout=25),201)
test=initial['test']
classic_url=service+'/api/v2/findings/'
before=verify(requests.get(classic_url,headers=classic_headers,params={'test':test},timeout=10),200)
assert before['count']==1
finding=before['results'][0]['id']
report_path=f'/commits/{recovered["commit"]}/reports/'

def classic_reimport():
    return verify(requests.post(service+'/api/v2/reimport-scan/',headers=classic_headers,data={'test':test,'scan_type':scanner,'deduplication_execution_mode':'sync'},files=file,timeout=30),201)['test']

def patch_finding():
    return verify(requests.patch(f'{classic_url}{finding}/',headers=classic_headers,json={'false_p':True},timeout=15),200)['false_p']

def request_export():
    answer=requests.post(api+report_path,headers=headers,json={'scan_ids':[recovered['scan']]},timeout=15)
    return verify(answer,202)['id']

def scoped_reads():
    ua=requests.Session()
    ua.headers.update(host)
    login=ua.get(service+'/login',timeout=8)
    from re import search
    csrf=search(r'name="csrfmiddlewaretoken" value="([^"]+)"',login.text).group(1)
    result=ua.post(service+'/login',data={**admin,'csrfmiddlewaretoken':csrf},headers={'Referer':'http://127.0.0.1/login'},timeout=8,allow_redirects=False)
    assert result.status_code==302 and 'sessionid' in ua.cookies
    return [ua.get(service+x,timeout=10,allow_redirects=False).status_code for x in ('/workspace/projects','/workspace/reports','/workspace/classic')]

with ThreadPoolExecutor(max_workers=5) as pool:
    jobs=[pool.submit(fn) for fn in (classic_reimport, patch_finding, request_export, scoped_reads, lambda:submit(8))]
    reimport,patched,report,read_statuses,submitted=[job.result() for job in jobs]
assert test==reimport and patched and read_statuses==[200,200,200]
assert verify(requests.get(f'{classic_url}{finding}/',headers=classic_headers,timeout=10),200)['false_p']
assert verify(requests.get(classic_url,headers=classic_headers,params={'test':test},timeout=10),200)['count']==1
assert not verify(requests.get(service+f'/api/v2/engagements/{engagement["id"]}/',headers=classic_headers,timeout=10),200).get('commit_hash')
for _ in range(40):
    scan=get('/scans/'+submitted['scan']+'/').json()
    reports=get(report_path).json()
    generated=next(row for row in reports if row['id']==report)
    assert scan['status']!='FAILED' and generated['status']!='FAILED'
    if scan['status']==generated['status']=='COMPLETED':
        break
    time.sleep(1)
assert scan['status']==generated['status']=='COMPLETED' and scan['finding_count']==1
print(json.dumps({'classic_import':201,'classic_reimport':201,'same_classic_test':True,'single_classic_finding':True,'false_positive_patch_preserved':True,'classic_has_no_git_context':True,'ui_reads':read_statuses,'new_scan_completed':True,'concurrent_report_completed':True},indent=2))
