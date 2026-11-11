"""Same-port, same-copy R5/RC comparison with inherited workload and resource guards.
Never runs migrations, background tasks or database writes other than sessions.
"""
import argparse
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HISTORY = ROOT / 'perf-report/round5'
OUT = ROOT / 'release/1.0.1/measurements'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--compose', type=Path, required=True)
p.add_argument('--credentials', type=Path, required=True)
p.add_argument('--phase', choices=['endpoints','mixed','profile'], required=True)
p.add_argument('--variants', default='round5,ui')
p.add_argument('--levels', default='1,5,10,15,25')
p.add_argument('--repeats', type=int, default=2)
p.add_argument('--requests', type=int)
p.add_argument('--label-prefix')
p.add_argument('--stop-file', type=Path, required=True)
a = p.parse_args()
credentials = a.credentials.read_bytes()
accounts = json.loads(credentials)
build = json.loads((OUT/'build-final.json').read_text())
release_build = json.loads((OUT/'build-rc.json').read_text())
images = {'original':'dd-final-original:3.5.100','round5':'dd-r5-final:3.5.100','ui':build['images']['app']['tag'],'rc':release_build['images']['app']['tag']}
sources = {'original':'334bef02d65a74909fe976b22724526474d5a0f6','round5':'c6a6144ed93b83adb1fd4ea9daa2c5e417ecea37','ui':build['source_sha'],'rc':release_build['source_sha']}
compose = json.loads(a.compose.read_text())
compose['services']['nginx']['image'] = build['images']['nginx']['tag']
raw=OUT/'raw';raw.mkdir(exist_ok=True)
web='aspm-rc1-aspm-1'

def run(argv, **kw):return subprocess.run(argv, check=True, **kw)
def ready():
 for _ in range(90):
  try:
   conn=http.client.HTTPConnection('127.0.0.1',48086,timeout=3)
   conn.request('GET',f'/api/v2/findings/{accounts[0]["finding"]}/',headers={'Authorization':'Token '+accounts[0]['token']})
   r=conn.getresponse();r.read();conn.close()
   if r.status==200:return
  except (OSError,http.client.HTTPException):pass
  time.sleep(1)
 raise RuntimeError('App not ready')

with (raw/(a.phase+'-controller.log')).open('a',buffering=1) as log:
 for rep in range(1,a.repeats+1):
  variants=a.variants.split(',');variants=variants if rep%2 else variants[::-1]
  for variant in variants:
   compose['services']['aspm']['image']=images[variant]
   compose['services']['nginx']['image']=(release_build if variant=='rc' else build)['images']['nginx']['tag']
   compose['services']['aspm'].setdefault('environment',{})['DD_FINAL_CACHE_PREFIX']=f'aspm-{a.label_prefix or a.phase}-{variant}-{rep}'
   a.compose.write_text(json.dumps(compose,indent=2)+'\n')
   run(['docker','compose','-p','aspm-rc1','-f',str(a.compose),'up','-d','aspm'],stdout=log,stderr=log)
   run(['docker','compose','-p','aspm-rc1','-f',str(a.compose),'restart','nginx'],stdout=log,stderr=log)
   ready()
   actual=subprocess.check_output(['docker','inspect','--format','{{.Image}}',web],text=True).strip()
   expected=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',images[variant]],text=True).strip()
   if actual!=expected:raise RuntimeError('Wrong app image')
   label=f'{a.label_prefix or a.phase}-r{rep}-{variant}'
   if a.phase=='profile':
    for name,target in [('profile.py','/tmp/r4-profile.py'),('scenarios.json','/tmp/r4-scenarios.json')]:run(['docker','cp',str(Path(__file__).with_name('profile_release.py') if name=='profile.py' else HISTORY/name),web+':'+target],stdout=log,stderr=log)
    r=run(['docker','exec','-i','-e','DD_FINAL_VARIANT='+variant,web,'python','manage.py','shell','-c',"exec(open('/tmp/r4-profile.py').read())"],input=credentials,stdout=subprocess.PIPE,stderr=log)
    lines=r.stdout.decode().splitlines()
    (OUT/f'profile-{variant}.json').write_text(json.dumps([json.loads(x[8:]) for x in lines if x.startswith('PROFILE ')],indent=2)+'\n')
    (OUT/f'plans-{variant}.json').write_text(json.dumps([json.loads(x[5:]) for x in lines if x.startswith('PLAN ')],indent=2)+'\n')
    print('PROFILE',variant,flush=True);continue
   env={**os.environ,'DD_FINAL_DB':'aspm_rc1_validation','DD_FINAL_REDIS_DB':'12','DD_FINAL_WORKER':'aspm-unused-worker'}
   monitor=subprocess.Popen([sys.executable,str(Path(__file__).with_name('monitor_release.py')),str(raw/(label+'-metrics.jsonl')),str(a.stop_file),'3600',web],env=env,stdout=log,stderr=log)
   run(['docker','exec',web,'python','-c',"from pathlib import Path;Path('/tmp/dd-r4-rss-stop').unlink(missing_ok=True)"],stdout=log,stderr=log)
   rss_stream=(raw/(label+'-rss.jsonl')).open('wb')
   rss=subprocess.Popen(['docker','exec','-i','-e','DD_RSS_DURATION=3600',web,'python','-'],stdin=subprocess.PIPE,stdout=rss_stream,stderr=log)
   rss.stdin.write((HISTORY/'worker_rss.py').read_bytes());rss.stdin.close()
   try:
    cases=['dashboard','web_findings','web_test','web_products','findings','products','tests'] if a.phase=='endpoints' else ['mixed']
    for level in ([1] if a.phase=='endpoints' else map(int,a.levels.split(','))):
     for case in cases:
      output=raw/f'{label}-c{level}-{case}.json'
      argv=[sys.executable,str(HISTORY/'benchmark.py'),'--url','http://127.0.0.1:48086','--scenarios',str(HISTORY/'scenarios.json'),'--variant',variant,'--concurrency',str(level),'--requests',str(a.requests or (60 if a.phase=='endpoints' else 300)),'--warmup',str(5 if a.phase=='endpoints' else 25),'--seconds','360','--timeout','90','--seed',str(35100+rep),'--scenario',case,'--stop-file',str(a.stop_file),'--output',str(output)]
      run(argv,input=credentials,stdout=log,stderr=log)
      result=json.loads(output.read_text());result.update(image_id=actual,rep=rep,phase=a.label_prefix or a.phase,source_sha=sources[variant])
      output.write_text(json.dumps(result,indent=2)+'\n')
      print(label,level,case,result['requests'],result['p95_ms'],result['rps'],flush=True)
      if a.stop_file.exists():raise RuntimeError('Resource guard stopped run')
   finally:
    run(['docker','exec',web,'touch','/tmp/dd-r4-rss-stop'],stdout=log,stderr=log)
    try:rss.wait(timeout=5)
    except subprocess.TimeoutExpired:rss.terminate()
    rss_stream.close();monitor.terminate()
    try:monitor.wait(timeout=8)
    except subprocess.TimeoutExpired:monitor.kill()
