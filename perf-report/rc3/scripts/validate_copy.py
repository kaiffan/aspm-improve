"""Real browser/import/reimport/rollback, only on a new isolated validation copy."""
import copy
import hashlib
import http.client
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
from urllib.parse import urlsplit,urlunsplit
from lab import ROOT, OUT, PRIVATE, RC2_PRIVATE, PG, WEB, run, save, compose, switch, fingerprint

assert json.loads((OUT/'raw/campaign-complete.json').read_text())['complete']
assert json.loads((OUT/'raw/sql-audit-complete.json').read_text())['complete']
DB='aspm_rc3_validation'
MEDIA='aspm-rc3_validation_media'
NODE_MODULES=RC2_PRIVATE.parent/'aspm-1.0.1-rc2/release/1.0.1/browser/node_modules'
log=(PRIVATE/'validation.log').open('a',buffering=1)
(OUT/'screenshots').mkdir(exist_ok=True)
run([sys.executable,str(OUT/'scripts/process_profiles.py')],stdout=log,stderr=log)


def pg_mutation(statement):
    run(['docker','exec','-e','RC3_SQL='+statement,PG,'sh','-c',
        'psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$RC3_SQL"'],stdout=log,stderr=log)


def shell(code,data=None):
    result=subprocess.check_output(['docker','exec','-i',WEB,'python','manage.py','shell','-c',code],input=data,stderr=log)
    return json.loads(next(line[7:] for line in result.decode().splitlines() if line.startswith('RESULT ')))


def configure(variant='rc3',worker=False):
    base=json.loads((RC2_PRIVATE/'base.compose.json').read_text())
    app=base['services']['aspm'];env=app['environment'];url=urlsplit(env['DD_DATABASE_URL'])
    env['DD_DATABASE_URL']=urlunsplit(url._replace(path='/'+DB))
    env['DD_CACHE_URL']='redis://rc2-cache:6379/1';env['DD_CELERY_BROKER_URL']='redis://rc2-cache:6379/0'
    env['DD_FINAL_CACHE_PREFIX']='rc3-validation'
    env.pop('DD_ASPM_GIT_SHA',None);env.pop('DD_ASPM_BUILD_TIMESTAMP',None)
    manifest=json.loads((OUT/'raw/build-final.json').read_text()) if variant=='rc3' else None
    app['image']=manifest['images']['app']['tag'] if manifest else 'aspm-build:25fb63ae7b48'
    base['services']['nginx']['image']=manifest['images']['nginx']['tag'] if manifest else 'aspm-nginx-build:25fb63ae7b48'
    app['volumes']=['validation-media:/app/media',str(PRIVATE/'validation-settings')+':/app/docker/extra_settings:ro']
    base['volumes']={'validation-media':{'external':True,'name':MEDIA}}
    base['services']['nginx']['ports']=['127.0.0.1:48092:8080']
    base['services']['nginx']['volumes']=[str(PRIVATE/'nginx.conf')+':/tmp/aspm-nginx.conf:ro']
    task_worker=copy.deepcopy(app)
    task_worker['entrypoint']=['/entrypoint-celery-worker.sh']
    task_worker['environment'].update(DD_CELERY_WORKER_POOL_TYPE='prefork',DD_CELERY_WORKER_PREFETCH_MULTIPLIER='1',DD_CELERY_WORKER_CONCURRENCY='1',DD_CELERY_WORKER_AUTOSCALE_MIN='1',DD_CELERY_WORKER_AUTOSCALE_MAX='1')
    base['services']['worker']=task_worker
    save(PRIVATE/'compose.json',base,True)
    compose('up','-d','aspm','nginx','rc2-cache',*(['worker'] if worker else []),stdout=log,stderr=log)
    compose('restart','nginx',stdout=log,stderr=log)
    from lab import ready
    ready()


def browser(name,source,replacements=(),**extra):
    text=source.read_text()
    for before,after in replacements:text=text.replace(before,after)
    path=PRIVATE/(name+'.cjs');path.write_text(text)
    env={**os.environ,'NODE_PATH':str(NODE_MODULES),'ASPM_URL':'http://127.0.0.1:48092',
        'ASPM_CREDENTIALS':str(PRIVATE/'accounts-copy.json'),**extra}
    run(['node',str(path)],cwd=ROOT,env=env,stdout=log,stderr=log)


def request(path,account):
    connection=http.client.HTTPConnection('127.0.0.1',48092,timeout=90)
    connection.request('GET',path,headers={'Authorization':'Token '+account['token']})
    response=connection.getresponse();body=response.read();status=response.status;connection.close()
    return status,body


if not (OUT/'raw/validation-prepared.json').exists():
    from lab import pg
    assert DB not in pg('SELECT datname FROM pg_database').splitlines(), 'Existing DB is preserved'
    compose('stop','aspm','nginx',stdout=log,stderr=log)
    pg_mutation('CREATE DATABASE '+DB+' TEMPLATE dd_round4_seed')
    run(['docker','volume','create',MEDIA],stdout=log,stderr=log)
    run(['docker','run','--rm','--user','root','--entrypoint','sh','-v','aspm-rc2_aspm_rc2_media:/from:ro','-v',MEDIA+':/to',
        'aspm-build:25fb63ae7b48','-c','cp -a /from/. /to/'],stdout=log,stderr=log)
    save(OUT/'raw/validation-prepared.json',{'database':DB,'template':'dd_round4_seed','independent_media_volume':MEDIA,'source_media_read_only':True})
target=PRIVATE/'validation-settings';target.mkdir(exist_ok=True);target.chmod(0o755)
shutil.copyfile(OUT/'scripts/task_metrics.py',target/'rc3_tasks.py')
(target/'local_settings.py').write_text("import os,sys\nEMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'\nCACHES['default']['KEY_PREFIX']=os.environ.get('DD_FINAL_CACHE_PREFIX','rc3-validation')\nsys.path.insert(0,'/app/docker/extra_settings')\nimport rc3_tasks\n")
for p in target.iterdir():p.chmod(0o644)
shutil.copyfile(PRIVATE/'accounts.json',PRIVATE/'accounts-copy.json');(PRIVATE/'accounts-copy.json').chmod(0o600)
configure(worker=True)
state=shell("""import json
from django.db import connection
from dojo.models import System_Settings
assert connection.settings_dict['NAME']=='aspm_rc3_validation'
settings=System_Settings.objects.get(no_cache=True);before=settings.enable_deduplication
settings.enable_deduplication=True;settings.save(update_fields=['enable_deduplication'])
print('RESULT '+json.dumps({'dedup_before':before,'database':connection.settings_dict['NAME']}))""")
try:
    import_script=PRIVATE/'import-smoke.py'
    import_script.write_text((ROOT/'release/1.0.1/scripts/import_smoke.py').read_text().replace('48086','48092').replace('ASPM RC1','ASPM RC3').replace('aspm-rc1.invalid','aspm-rc3.invalid'))
    result=OUT/'raw/import-smoke.json'
    if not result.exists():
        run([sys.executable,str(import_script),'rc3-20261112',str(result),'--rounds','1'],input=(PRIVATE/'accounts-copy.json').read_bytes(),stdout=log,stderr=log)
    steps=json.loads(result.read_text())
    assert len(steps)==3 and all(row['status']==201 and row['deduplication_complete'] for row in steps)
finally:
    shell("""import json,sys
from django.db import connection
from dojo.models import System_Settings
assert connection.settings_dict['NAME']=='aspm_rc3_validation'
settings=System_Settings.objects.get(no_cache=True);settings.enable_deduplication=json.load(sys.stdin);settings.save(update_fields=['enable_deduplication'])
print('RESULT '+json.dumps({'restored':settings.enable_deduplication}))""",json.dumps(state['dedup_before']).encode())
save(OUT/'raw/import-isolation.json',state)
test,peer=steps[0]['test'],steps[2]['test']
prior_finding=json.loads((OUT/'raw/browser-write-checks.json').read_text())['finding'] if (OUT/'raw/browser-write-checks.json').exists() else None
save(PRIVATE/'write-context.json',{'test':test,'finding':prior_finding},True)
if not (PRIVATE/'login.json').exists():
    login={'username':'rc3_access_free_20261112','password':secrets.token_urlsafe(32)}
    login.update(shell("""import json,sys
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.authtoken.models import Token
assert connection.settings_dict['NAME']=='aspm_rc3_validation'
secret=json.load(sys.stdin);User=get_user_model();assert not User.objects.filter(username=secret['username']).exists()
user=User.objects.create_user(secret['username'],password=secret['password'],is_active=True,is_staff=False,is_superuser=False)
print('RESULT '+json.dumps({'token':Token.objects.create(user=user).key}))""",json.dumps(login).encode()))
    save(PRIVATE/'login.json',login,True)
browser('writes',ROOT/'release/1.0.1/browser/write_checks.cjs',[
    ('48086','48092'),('ASPM RC1','ASPM RC3'),('aspm rc1','aspm rc3'),('2026-11-11','2026-11-12'),
    ('release/1.0.1/screenshots/',str(OUT/'screenshots')+'/'),('release/1.0.1/measurements/',str(OUT/'raw')+'/')],
    ASPM_WRITE_CONTEXT=str(PRIVATE/'write-context.json'),ASPM_LOGIN_CREDENTIALS=str(PRIVATE/'login.json'))
finding=json.loads((OUT/'raw/browser-write-checks.json').read_text())['finding']
verification=shell("""import json,sys
from dojo.models import Finding,BurpRawRequestResponse
from dojo.location.models import LocationFindingReference
d=json.load(sys.stdin);primary=Finding.objects.filter(test_id=d['test']);peer=Finding.objects.filter(test_id=d['peer'])
print('RESULT '+json.dumps({'primary_count':primary.exclude(pk=d['finding']).count(),'mitigated':primary.filter(is_mitigated=True).count(),'peer_count':peer.count(),'peer_duplicates':peer.filter(duplicate=True).count(),'locations':LocationFindingReference.objects.filter(finding__test_id=d['test']).count(),'evidence_rows':BurpRawRequestResponse.objects.filter(finding__test_id=d['test']).count()}))""",json.dumps({'test':test,'peer':peer,'finding':finding}).encode())
assert verification['primary_count']==44 and verification['mitigated']==4 and verification['peer_count']==verification['peer_duplicates']==40
accounts=json.loads((PRIVATE/'accounts-copy.json').read_text())
status,body=request(f'/api/v2/findings/{finding}/',accounts[0]);assert status==200;detail=json.loads(body)
status,body=request(f'/api/v2/findings/?id={finding}',accounts[0]);assert status==200;listing=json.loads(body)
assert detail['vulnerability_ids']==listing['results'][0]['vulnerability_ids'] and len(detail['vulnerability_ids'])==2
verification.update(finding=finding,vulnerability_ids=detail['vulnerability_ids'])
save(OUT/'raw/import-verification.json',verification)
browser('audit',ROOT/'release/1.0.1/browser/validate.cjs',[("const root='release/1.0.1';",'const root='+json.dumps(str(OUT))+';'),('/measurements/','/raw/')])
browser('regression',ROOT/'release/1.0.1/browser/rc2_regression.cjs',ASPM_OUTPUT=str(OUT/'raw/browser-regression.json'))
browser('rapid',ROOT/'release/1.0.1/rc2/scripts/rapid.cjs',[('release/1.0.1/rc2/raw/',str(OUT/'raw')+'/')])
browser('expanded',ROOT/'release/1.0.1/rc2/scripts/expanded.cjs',[('release/1.0.1/rc2/',str(OUT)+'/')])
run(['docker','cp',str(ROOT/'release/1.0.1/rc2/scripts/ui_matrix.py'),WEB+':/tmp/rc3-ui-matrix.py'],stdout=log,stderr=log)
matrix=subprocess.check_output(['docker','exec','-i',WEB,'python','manage.py','shell','-c',"exec(open('/tmp/rc3-ui-matrix.py').read())"],input=(PRIVATE/'accounts-copy.json').read_bytes(),stderr=log).decode()
save(OUT/'raw/ui-matrix.json',json.loads(next(line[7:] for line in matrix.splitlines() if line.startswith('MATRIX '))))
drain=[]
consecutive_empty=0
for _ in range(30):
    counts=shell("""import json
from dojo.celery import app
inspector=app.control.inspect(timeout=2)
states={name:getattr(inspector,name)() for name in ['active','reserved','scheduled']}
print('RESULT '+json.dumps({name:sum(len(tasks) for tasks in workers.values()) if workers else None for name,workers in states.items()}))""")
    counts['queued']=int(subprocess.check_output(['docker','exec','aspm-rc3-rc2-cache-1','valkey-cli','-n','0','LLEN','celery'],text=True).strip())
    drain.append(counts)
    consecutive_empty=consecutive_empty+1 if all(value==0 for value in counts.values()) else 0
    if consecutive_empty>=2:break
    time.sleep(2)
else:raise RuntimeError('Outstanding/unreachable tasks: preserve worker and postpone rollback')
save(OUT/'raw/celery-drain.json',drain)
run(['docker','cp','aspm-rc3-worker-1:/tmp/rc3-task-metrics.jsonl',str(OUT/'raw/celery-tasks.jsonl')],stdout=log,stderr=log)
task_rows=[json.loads(line) for line in (OUT/'raw/celery-tasks.jsonl').read_text().splitlines() if line]
assert task_rows and not any(row['state']=='FAILURE' for row in task_rows), 'Investigate task failures before promotion'
compose('stop','worker',stdout=log,stderr=log)
snapshots={}
for variant in ['rc2','rc3']:
    configure(variant)
    for actor in [0,1]:
        account=accounts[actor]
        cases=['/api/v2/findings/?limit=100','/api/v2/findings/?limit=100&offset=500000&fast_offset=1',f'/api/v2/findings/{account["finding"]}/',f'/api/v2/findings/?test__engagement__product={account["product"]}&severity=High&active=true&limit=100','/api/v2/products/?limit=100','/api/v2/products/?findings=count','/api/v2/products/?findings=none','/api/v2/tests/?limit=100','/api/v2/engagements/?limit=100']
        for path in cases:
            status,body=request(path,account);assert status==200
            snapshots[variant,actor,path]={'status':status,'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}
comparisons=[{'actor':actor,'path':path,'equal':value==snapshots['rc2',actor,path]} for (variant,actor,path),value in snapshots.items() if variant=='rc3']
assert len(comparisons)==18 and all(row['equal'] for row in comparisons)
save(OUT/'raw/rollback-check.json',{'pairs':18,'database':DB,'comparisons':comparisons,'restored_source_sha':json.loads((OUT/'raw/build-final.json').read_text())['source_sha']})
# Remove diagnostic task hooks before leaving a reviewable demo running.
(target/'local_settings.py').write_text("import os\nEMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'\nCACHES['default']['KEY_PREFIX']=os.environ.get('DD_FINAL_CACHE_PREFIX','rc3-validation')\n")
configure(worker=True)
compose('restart','aspm','worker','nginx',stdout=log,stderr=log)
from lab import ready
ready()
checks={}
for name,args in [('django_check',['check']),('migration_check',['makemigrations','--check','--dry-run']),('openapi',['spectacular','--fail-on-warn'])]:
    result=subprocess.run(['docker','exec',WEB,'python','manage.py',*args],capture_output=True,text=True)
    (PRIVATE/(name+'.log')).write_text(result.stdout+result.stderr)
    checks[name]={'exit_code':result.returncode};assert result.returncode==0,name
save(OUT/'raw/management-checks.json',checks)
fingerprint('final')
save(OUT/'raw/validation-complete.json',{'complete':True,'database':DB,'port':48092,'measurement_middleware_removed':True,'task_instrumentation_removed':True,'worker_concurrency':1,'worker_prefetch':1,'source_unchanged':True})
print('Browser/import/reimport/evidence/rollback validation complete',flush=True)
