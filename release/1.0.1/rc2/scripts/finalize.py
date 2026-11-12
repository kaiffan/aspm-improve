"""Finish correctness, actual browser, real importer and rollback on the write copy."""
import copy
import hashlib
import http.client
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from common import OUT, PRIVATE, ROOT, SOURCE, WEB, app_config, compose, output, pg, run, save, shell, switch

while not (OUT/'raw/campaign-complete.json').exists():time.sleep(10)
assert json.loads((OUT/'raw/campaign-complete.json').read_text())['source_sha']==SOURCE
log=(PRIVATE/'finalization.log').open('a',buffering=1)
browser_env={**os.environ,'NODE_PATH':str(ROOT/'release/1.0.1/browser/node_modules'),'ASPM_URL':'http://127.0.0.1:48091','ASPM_CREDENTIALS':str(PRIVATE/'accounts.json')}


def browser(name, original, replacements=(), **env):
    text=Path(original).read_text()
    for before,after in replacements:text=text.replace(before,after)
    script=PRIVATE/(name+'.cjs');script.write_text(text)
    return subprocess.run(['node',str(script)],cwd=ROOT,env={**browser_env,**env},stdout=log,stderr=log).returncode


def decoded(code,data=None):
    text=shell(code,data=data).decode()
    return json.loads(next(line[7:] for line in text.splitlines() if line.startswith('RESULT ')))


def add_worker():
    config=json.loads((PRIVATE/'compose.json').read_text())
    assert config['services']['aspm']['environment']['DD_DATABASE_URL'].endswith('/aspm_rc2_validation')
    worker=copy.deepcopy(config['services']['aspm'])
    worker['entrypoint']=['/entrypoint-celery-worker.sh']
    worker['environment'].update(DD_CELERY_WORKER_POOL_TYPE='prefork',DD_CELERY_WORKER_PREFETCH_MULTIPLIER='1',DD_CELERY_WORKER_CONCURRENCY='1',DD_CELERY_WORKER_AUTOSCALE_MIN='1',DD_CELERY_WORKER_AUTOSCALE_MAX='1')
    config['services']['worker']=worker
    save(PRIVATE/'compose.json',config,private=True)
    compose('up','-d','worker',stdout=log,stderr=log)


# Real pre-fix browser proof, kept apart from measurements and final screenshots.
switch('rc1',prefix='rc2-browser-before')
code=browser('p0-before',ROOT/'release/1.0.1/browser/rc2_regression.cjs',ASPM_OUTPUT=str(OUT/'raw/browser-p0-before.json'))
before=json.loads((OUT/'raw/browser-p0-before.json').read_text())
assert code!=0 and any(not r['pass'] for r in before)

# The write copy already exists; never replace or rebuild it.
switch('rc2','aspm_rc2_validation',False,'rc2-demo-final')
if not (PRIVATE/'accounts-copy.json').exists():
    run([sys.executable,str(ROOT/'perf-report/final/prepare_credentials.py'),'--container',WEB,'--output',str(PRIVATE/'accounts-copy.json')],stdout=log,stderr=log)
browser_env['ASPM_CREDENTIALS']=str(PRIVATE/'accounts-copy.json')
assert browser('p0-after',ROOT/'release/1.0.1/browser/rc2_regression.cjs',ASPM_OUTPUT=str(OUT/'raw/browser-p0-after.json'))==0
assert browser('audit',ROOT/'release/1.0.1/browser/validate.cjs',[("const root='release/1.0.1';","const root='release/1.0.1/rc2';"),('/measurements/','/raw/')])==0
assert browser('expanded',OUT/'scripts/expanded.cjs')==0

# Native navigation timings are descriptive; they are not a 16-sample p95 claim.
nav=(ROOT/'release/1.0.1/browser/performance.cjs').read_text()
nav=nav.replace("for(const variant of(rep===1?['round5','ui']:['ui','round5']))", "for(const variant of ['rc2'])")
nav=nav.replace("const url=variant==='round5'?'http://127.0.0.1:48089':'http://127.0.0.1:48086'", "const url='http://127.0.0.1:48091'")
nav=nav.replace('release/1.0.1/measurements/browser-performance.json','release/1.0.1/rc2/raw/browser-performance.json')
path=PRIVATE/'navigation.cjs';path.write_text(nav)
run(['node',str(path)],cwd=ROOT,env=browser_env,stdout=log,stderr=log)

run(['docker','cp',str(OUT/'scripts/ui_matrix.py'),WEB+':/tmp/rc2-ui-matrix.py'],stdout=log,stderr=log)
data=shell("exec(open('/tmp/rc2-ui-matrix.py').read())",(PRIVATE/'accounts-copy.json').read_bytes()).decode()
save(OUT/'raw/ui-matrix.json',json.loads(next(line[7:] for line in data.splitlines() if line.startswith('MATRIX '))))

# Synthetic scan contents, but the supported real API/importer/deduplicator path.
assert output(['docker','exec','aspm-rc2-rc2-cache-1','valkey-cli','-n','0','LLEN','celery'])=='0'
dedup=decoded("""import json
from django.db import connection
from dojo.models import System_Settings
assert connection.settings_dict['NAME']=='aspm_rc2_validation'
obj=System_Settings.objects.get(no_cache=True)
before=obj.enable_deduplication
obj.enable_deduplication=True;obj.save(update_fields=['enable_deduplication'])
print('RESULT '+json.dumps({'before':before,'during':True}))
""")
try:
    add_worker()
    text=(ROOT/'release/1.0.1/scripts/import_smoke.py').read_text().replace('48086','48091').replace('ASPM RC1','ASPM RC2 recovery').replace('aspm-rc1.invalid','aspm-rc2.invalid')
    script=PRIVATE/'import-smoke.py';script.write_text(text)
    if not (OUT/'raw/import-smoke.json').exists():
        run([sys.executable,str(script),'recovered-20261112',str(OUT/'raw/import-smoke.json'),'--rounds','1'],input=(PRIVATE/'accounts-copy.json').read_bytes(),stdout=log,stderr=log)
    else:
        existing=json.loads((OUT/'raw/import-smoke.json').read_text())
        assert len(existing)==3 and all(x['status']==201 and x['deduplication_complete'] for x in existing),'Inspect incomplete importer evidence before resuming'
finally:
    restored=decoded("""import json,sys
from django.db import connection
from dojo.models import System_Settings
assert connection.settings_dict['NAME']=='aspm_rc2_validation'
value=json.load(sys.stdin)
obj=System_Settings.objects.get(no_cache=True)
obj.enable_deduplication=value;obj.save(update_fields=['enable_deduplication'])
print('RESULT '+json.dumps({'restored':obj.enable_deduplication}))
""",json.dumps(dedup['before']).encode())
    save(OUT/'raw/import-isolation.json',{**dedup,**restored,'database':'aspm_rc2_validation'})

steps=json.loads((OUT/'raw/import-smoke.json').read_text())
test=steps[0]['test'];peer=steps[2]['test']
prior_finding=json.loads((OUT/'raw/browser-write-checks.json').read_text())['finding'] if (OUT/'raw/browser-write-checks.json').exists() else None
save(PRIVATE/'write-context.json',{'test':test,'finding':prior_finding},private=True)
if (PRIVATE/'login.json').exists():
    login=json.loads((PRIVATE/'login.json').read_text())
else:
    login={'username':'rc2_recovered_access_free_20261112','password':secrets.token_urlsafe(32)}
    login.update(decoded("""import json,sys
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.authtoken.models import Token
assert connection.settings_dict['NAME']=='aspm_rc2_validation'
secret=json.load(sys.stdin);User=get_user_model()
assert not User.objects.filter(username=secret['username']).exists(),'Existing account preserved'
user=User.objects.create_user(secret['username'],password=secret['password'],is_active=True,is_staff=False,is_superuser=False)
token=Token.objects.create(user=user)
print('RESULT '+json.dumps({'token':token.key}))
""",json.dumps(login).encode()))
    save(PRIVATE/'login.json',login,private=True)
assert browser('writes',ROOT/'release/1.0.1/browser/write_checks.cjs',[
    ('48086','48091'),('ASPM RC1','ASPM RC2 recovery'),('aspm rc1','aspm rc2 recovery'),
    ('2026-11-11','2026-11-12'),('release/1.0.1/screenshots/','release/1.0.1/rc2/screenshots/'),
    ('release/1.0.1/measurements/','release/1.0.1/rc2/raw/')],
    ASPM_WRITE_CONTEXT=str(PRIVATE/'write-context.json'),ASPM_LOGIN_CREDENTIALS=str(PRIVATE/'login.json'))==0
finding=json.loads((OUT/'raw/browser-write-checks.json').read_text())['finding']
verification=decoded("""import json,sys
from dojo.models import Finding
from dojo.location.models import LocationFindingReference
d=json.load(sys.stdin);primary=Finding.objects.filter(test_id=d['test']);peer=Finding.objects.filter(test_id=d['peer'])
print('RESULT '+json.dumps({'primary_count':primary.exclude(pk=d['finding']).count(),'mitigated':primary.filter(is_mitigated=True).count(),'peer_count':peer.count(),'peer_duplicates':peer.filter(duplicate=True).count(),'locations':LocationFindingReference.objects.filter(finding__test_id=d['test']).count()}))
""",json.dumps({'test':test,'peer':peer,'finding':finding}).encode())
assert verification['primary_count']==44 and verification['mitigated']==4 and verification['peer_count']==40 and verification['peer_duplicates']==40
accounts=json.loads((PRIVATE/'accounts-copy.json').read_text())


def request(path,account):
    conn=http.client.HTTPConnection('127.0.0.1',48091,timeout=90)
    conn.request('GET',path,headers={'Authorization':'Token '+account['token']})
    response=conn.getresponse();body=response.read();status=response.status;conn.close()
    return status,body


status,body=request(f'/api/v2/findings/{finding}/',accounts[0]);assert status==200
detail=json.loads(body);status,body=request(f'/api/v2/findings/?id={finding}',accounts[0]);assert status==200
listing=json.loads(body);assert listing['count']==1
assert detail['vulnerability_ids']==listing['results'][0]['vulnerability_ids'] and len(detail['vulnerability_ids'])==2
verification.update(finding=finding,vulnerability_ids=detail['vulnerability_ids'])
save(OUT/'raw/import-verification.json',verification)
for _ in range(60):
    if output(['docker','exec','aspm-rc2-rc2-cache-1','valkey-cli','-n','0','LLEN','celery'])=='0':break
    time.sleep(1)
else:raise RuntimeError('Outstanding Celery tasks preserved; rollback postponed')
compose('stop','worker',stdout=log,stderr=log)

# Full byte comparison of standard and opt-in JSON on the identical write copy.
snapshots={}
for variant in ['rc1','rc2']:
    switch(variant,'aspm_rc2_validation',False,'rc2-rollback-'+variant)
    for actor in [0,1]:
        account=accounts[actor]
        cases=['/api/v2/findings/?limit=100','/api/v2/findings/?limit=100&offset=500000&fast_offset=1',f'/api/v2/findings/{account["finding"]}/',f'/api/v2/findings/?test__engagement__product={account["product"]}&severity=High&active=true&limit=100','/api/v2/products/?limit=100','/api/v2/products/?findings=count','/api/v2/products/?findings=none','/api/v2/tests/?limit=100','/api/v2/engagements/?limit=100']
        for path in cases:
            status,body=request(path,account);assert status==200
            snapshots[variant,actor,path]={'status':status,'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}
comparisons=[{'actor':actor,'path':path,'equal':value==snapshots['rc1',actor,path]} for (variant,actor,path),value in snapshots.items() if variant=='rc2']
assert len(comparisons)==18 and all(x['equal'] for x in comparisons)
save(OUT/'raw/rollback-check.json',{'pairs':18,'database':'aspm_rc2_validation','comparisons':comparisons,'restored_source_sha':SOURCE})
add_worker()

checks={}
for name,args in [('django_check',['check']),('migration_check',['makemigrations','--check','--dry-run']),('openapi',['spectacular','--fail-on-warn'])]:
    result=subprocess.run(['docker','exec',WEB,'python','manage.py',*args],capture_output=True,text=True)
    (PRIVATE/(name+'.log')).write_text(result.stdout+result.stderr)
    checks[name]={'exit_code':result.returncode}
    assert result.returncode==0,name
save(OUT/'raw/management-checks.json',checks)
save(OUT/'raw/finalization-complete.json',{'complete':True,'source_sha':SOURCE,'database':'aspm_rc2_validation','demo_port':48091,'instrumentation_removed':True,'worker_started':True,'release_alias_promoted':False})
print('Final browser/import/rollback/checks complete; release gates are evaluated separately',flush=True)
