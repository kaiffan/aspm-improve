"""Read-only same-copy rollback gate. No migrations or background processes."""
import argparse
import hashlib
import http.client
import json
from pathlib import Path
import subprocess
import time

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compose',type=Path,required=True);p.add_argument('--credentials',type=Path,required=True);a=p.parse_args()
R=Path(__file__).resolve().parents[1];m=json.loads((R/'measurements/build-rc.json').read_text());c=json.loads(a.compose.read_text());accounts=json.loads(a.credentials.read_text());rows={}
def command(argv):subprocess.run(argv,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def get(path,account,auth='token'):
 conn=http.client.HTTPConnection('127.0.0.1',48086,timeout=60);headers={'Authorization':'Token '+account['token']} if auth=='token' else {'Cookie':'sessionid='+account['session']};conn.request('GET',path,headers=headers);response=conn.getresponse();body=response.read();conn.close();return response.status,body
for variant,image in [('round5','dd-r5-final:3.5.100'),('rc',m['images']['app']['tag'])]:
 c['services']['aspm']['image']=image;c['services']['nginx']['image']=m['images']['nginx']['tag'];c['services']['aspm']['environment']['DD_FINAL_CACHE_PREFIX']='aspm-rollback-'+variant;a.compose.write_text(json.dumps(c,indent=2)+'\n')
 command(['docker','compose','-p','aspm-rc1','-f',str(a.compose),'up','-d','aspm','nginx']);command(['docker','compose','-p','aspm-rc1','-f',str(a.compose),'restart','nginx'])
 for _ in range(90):
  try:
   if get('/api/v2/tests/?limit=1',accounts[0])[0]==200:break
  except (OSError,http.client.HTTPException):pass
  time.sleep(1)
 else:raise RuntimeError('App not ready')
 check=subprocess.check_output(['docker','exec','aspm-rc1-aspm-1','python','manage.py','shell','-c',"from django.db import connection; assert connection.settings_dict['NAME']=='aspm_rc1_validation'; print('ISOLATED_OK')"],text=True)
 if 'ISOLATED_OK' not in check:raise RuntimeError('Wrong database')
 for actor in [0,1]:
  account=accounts[actor]
  cases=['/api/v2/findings/?limit=100','/api/v2/findings/?limit=100&offset=500000&fast_offset=1',f'/api/v2/findings/{account["finding"]}/',f'/api/v2/findings/?test__engagement__product={account["product"]}&severity=High&active=true&limit=100','/api/v2/products/?limit=100','/api/v2/products/?findings=count','/api/v2/products/?findings=none','/api/v2/tests/?limit=100','/api/v2/engagements/?limit=100']
  for path in cases:
   status,body=get(path,account);assert status==200
   rows[(variant,actor,path)]={'status':status,'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}
 comparisons=[]
 for (v,actor,path),value in list(rows.items()):
  if v=='rc':comparisons.append({'actor':actor,'path':path,'equal':value==rows['round5',actor,path]})
report={'source_sha':m['source_sha'],'database':'aspm_rc1_validation','rollback_started_and_healthy':True,'restored_rc_and_healthy':True,'pairs':len(comparisons),'comparisons':comparisons}
(R/'measurements/rollback-check.json').write_text(json.dumps(report,indent=2)+'\n');assert all(x['equal'] for x in comparisons);print('Rollback/restore verified;',len(comparisons),'full JSON pairs equal')
