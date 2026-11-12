"""Recover retained images/volumes; no migrations, seed writes or main-app changes."""
import json
import shutil
import sys
from common import OUT, PG, PRIVATE, ROOT, SOURCE, VARIANTS, output, pg, save, switch

OUT.joinpath('raw').mkdir(parents=True, exist_ok=True)
OUT.joinpath('charts').mkdir(exist_ok=True)
OUT.joinpath('screenshots').mkdir(exist_ok=True)
PRIVATE.mkdir(parents=True, exist_ok=True)
PRIVATE.chmod(0o700)
records = {x['Name'].lstrip('/'): x for x in json.loads((PRIVATE/'containers.json').read_text())}
old = records['aspm-rc2-aspm-1']
env = dict(x.split('=', 1) for x in old['Config']['Env'])
env = {k: v for k, v in env.items() if k.startswith('DD_')}
env['DD_CELERY_BROKER_URL'] = 'redis://rc2-cache:6379/0'
env['DD_CACHE_URL'] = 'redis://rc2-cache:6379/1'
for directory in ['demo', 'instrumented']:
    target = PRIVATE/directory
    target.mkdir(exist_ok=True)
    target.chmod(0o755)
    text = "import os\nEMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'\nCACHES['default']['KEY_PREFIX']=os.environ.get('DD_FINAL_CACHE_PREFIX','rc2-demo')\n"
    if directory == 'instrumented':
        shutil.copyfile(ROOT/'perf-report/round5/perf_instrument.py', target/'rc2_perf.py')
        text += "import sys\nsys.path.insert(0,'/app/docker/extra_settings')\nMIDDLEWARE=['rc2_perf.SQLMiddleware',*MIDDLEWARE]\n"
    (target/'local_settings.py').write_text(text)
    for p in target.iterdir(): p.chmod(0o644)
nginx = PRIVATE/'nginx.conf'
shutil.copyfile(ROOT/'release/1.0.1/nginx.conf', nginx)
nginx.chmod(0o644)
config = {'services': {
    'aspm': {'image':VARIANTS['rc2'][0], 'entrypoint':['/entrypoint-uwsgi.sh'],
             'environment':env, 'volumes':['media:/app/media', str(PRIVATE/'demo')+':/app/docker/extra_settings:ro'],
             'networks':['default','database']},
    'nginx': {'image':VARIANTS['rc2'][1], 'entrypoint':['nginx','-c','/tmp/aspm-nginx.conf','-g','daemon off;'],
              'ports':['127.0.0.1:48091:8080'], 'volumes':[str(nginx)+':/tmp/aspm-nginx.conf:ro'],
              'depends_on':['aspm']},
    'rc2-cache': {'image':'dd-api-perf-valkey:local'}},
    'volumes':{'media':{'external':True,'name':'aspm-rc2_aspm_rc2_media'}},
    'networks':{'database':{'external':True,'name':'django-defectdojo_default'}}}
save(PRIVATE/'base.compose.json',config,private=True)
sql = """SELECT json_build_object('findings',count(*),'original_ids',count(*) FILTER (WHERE id<=1000000),
'fixture_ids',count(*) FILTER (WHERE id>1000000),'sum_ids',sum(id)::text,
'rows_xor',bit_xor(hashtextextended(f::text,0))::text,'max_updated',max(updated),
'deduplication',(SELECT enable_deduplication FROM dojo_system_settings ORDER BY id LIMIT 1),
'database_bytes',pg_database_size(current_database())) FROM dojo_finding f"""
data = {db:json.loads(pg(sql,db)) for db in ['source','dd_round4_seed','aspm_rc2_validation']}
for key in ('findings','sum_ids','rows_xor','max_updated','deduplication'):
    assert data['source'][key] == data['dd_round4_seed'][key]
assert data['source']['findings'] == 1000168
save(OUT/'raw/dataset-before.json',data)
print('Original and protected seed: 1,000,168 rows; full-row fingerprints match',flush=True)
images={}
for variant,(app,static,sha) in VARIANTS.items():
    images[variant]={'source_sha':sha,'app':{},'nginx':{}}
    for kind,tag in [('app',app),('nginx',static)]:
        d=json.loads(output(['docker','image','inspect',tag]))[0]
        images[variant][kind]={'tag':tag,'id':d['Id'],'repo_digests':d.get('RepoDigests',[]),'labels':d['Config'].get('Labels',{})}
save(OUT/'build.json',{'source_sha':SOURCE,'variants':images,'recovered_retained_images':True})
switch('rc2',instrument=True,prefix='rc2-credential-recovery')
from common import run
run([sys.executable,str(ROOT/'perf-report/final/prepare_credentials.py'),'--container','aspm-rc2-aspm-1','--output',str(PRIVATE/'accounts.json')])
print('RC2 restored on port 48091 against the protected seed; workers remain stopped',flush=True)
