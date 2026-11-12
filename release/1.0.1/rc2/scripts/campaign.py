"""New comparable series after recovery: Latin-square order, all raw observations."""
import json
import os
import subprocess
import sys
import time
from common import OUT, PRIVATE, ROOT, SOURCE, VARIANTS, WEB, compose, run, save, switch

marker=OUT/'raw/tests-complete.json'
while not all(p.exists() for p in [marker, OUT/'raw/preload-ready.json', OUT/'raw/baseline-tests-complete.json']):
    time.sleep(10)
assert json.loads(marker.read_text())['source_sha']==SOURCE
credentials=(PRIVATE/'accounts.json').read_bytes()
base=ROOT/'perf-report/round5'
endpoint_cases=['dashboard','web_findings','web_test','web_products','findings','filtered_product','finding_detail','products','tests','engagements']
stop=PRIVATE/'benchmark-stop'
if stop.exists(): raise RuntimeError('Inspect resource stop before continuing')
if any((OUT/'raw').glob('mixed-r*-*-c*-mixed.json')) or any((OUT/'raw').glob('endpoints-r*-*-c*-*.json')):
    raise RuntimeError('Existing measured cohort preserved: archive it explicitly before a new series')
log=(OUT/'raw/campaign-console.log').open('a',buffering=1)

for phase in ['mixed','endpoints']:
    repeats=3 if phase=='mixed' else 2
    levels=[1,5,10,15,25] if phase=='mixed' else [1]
    for rep in range(1,repeats+1):
        variants=['round5','rc1','rc2']
        variants=variants[rep-1:]+variants[:rep-1]
        for variant in variants:
            image_id=switch(variant,prefix=f'rc2-recovered-{phase}-{variant}-{rep}')
            for level in levels:
                for case in (['mixed'] if phase=='mixed' else endpoint_cases):
                    label=f'{phase}-r{rep}-{variant}-c{level}-{case}'
                    env={**os.environ,'DD_FINAL_DB':'dd_round4_seed','DD_FINAL_VALKEY':'aspm-rc2-rc2-cache-1','DD_FINAL_REDIS_DB':'0','DD_FINAL_WORKER':'aspm-no-worker'}
                    monitor_log=(OUT/'raw/monitor-console.log').open('a')
                    monitor=subprocess.Popen([sys.executable,str(ROOT/'release/1.0.1/scripts/monitor_release.py'),str(OUT/'raw'/(label+'-metrics.jsonl')),str(stop),'900',WEB],env=env,stdout=monitor_log,stderr=monitor_log)
                    run(['docker','exec',WEB,'python','-c',"from pathlib import Path; Path('/tmp/dd-r4-rss-stop').unlink(missing_ok=True)"],stdout=log,stderr=log)
                    rss_log=(OUT/'raw'/(label+'-rss.jsonl')).open('wb')
                    rss=subprocess.Popen(['docker','exec','-i','-e','DD_RSS_DURATION=900',WEB,'python','-'],stdin=subprocess.PIPE,stdout=rss_log,stderr=log)
                    rss.stdin.write((base/'worker_rss.py').read_bytes());rss.stdin.close()
                    try:
                        target=OUT/'raw'/(label+'.json')
                        count=300 if phase=='mixed' else 60
                        argv=[sys.executable,str(base/'benchmark.py'),'--url','http://127.0.0.1:48091','--scenarios',str(base/'scenarios.json'),'--variant',variant,'--concurrency',str(level),'--requests',str(count),'--warmup',str(25 if phase=='mixed' else 5),'--seconds','480','--timeout','90','--seed',str(35100+rep),'--scenario',case,'--stop-file',str(stop),'--output',str(target)]
                        run(argv,input=credentials,stdout=log,stderr=log)
                        data=json.loads(target.read_text())
                        data.update(source_sha=VARIANTS[variant][2],image_id=image_id,rep=rep,phase=phase,campaign='recovered-2026-11-12')
                        save(target,data)
                        print(label,data['requests'],data['p95_ms'],data['rps'],flush=True)
                        if stop.exists(): raise RuntimeError('Resource guard stopped comparison')
                    finally:
                        run(['docker','exec',WEB,'touch','/tmp/dd-r4-rss-stop'],stdout=log,stderr=log)
                        try:rss.wait(timeout=3)
                        except subprocess.TimeoutExpired:rss.terminate()
                        rss_log.close();monitor.terminate()
                        try:monitor.wait(timeout=5)
                        except subprocess.TimeoutExpired:monitor.kill()
                        monitor_log.close()

for variant in ['round5','rc1','rc2']:
    switch(variant,prefix=f'rc2-recovered-profiles-{variant}')
    run(['docker','cp',str(OUT/'scripts/profile.py'),WEB+':/tmp/rc2-profile.py'],stdout=log,stderr=log)
    run(['docker','cp',str(base/'scenarios.json'),WEB+':/tmp/r4-scenarios.json'],stdout=log,stderr=log)
    result=run(['docker','exec','-i','-e','DD_FINAL_VARIANT='+variant,WEB,'python','manage.py','shell','-c',"exec(open('/tmp/rc2-profile.py').read())"],input=credentials,stdout=subprocess.PIPE,stderr=log)
    lines=result.stdout.decode().splitlines()
    save(OUT/f'profile-{variant}.json',[json.loads(line[8:]) for line in lines if line.startswith('PROFILE ')])
    save(OUT/f'plans-{variant}.json',[json.loads(line[5:]) for line in lines if line.startswith('PLAN ')])
    print('PROFILE',variant,flush=True)
save(OUT/'raw/campaign-complete.json',{'complete':True,'source_sha':SOURCE,'runs':105,'measured_requests':17100})
print('COMPARABLE CAMPAIGN COMPLETE',flush=True)
