"""Image/source/dependency/runtime evidence and local RC3 aliases; no publication."""
import hashlib
import http.client
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
from lab import ROOT,OUT,PRIVATE,WEB,run,save

assert json.loads((OUT/'raw/validation-complete.json').read_text())['complete']
build=json.loads((OUT/'raw/build-final.json').read_text())
context=Path(os.environ.get('RC3_BUILD_CONTEXT',PRIVATE/'build-final-test-count-guard'))
expected={str(path.relative_to(context)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (context/'dojo').rglob('*') if path.is_file()}
# The pinned entrypoint explicitly removes this documentation file at startup.
expected.pop('dojo/settings/README.md',None)
code="""import hashlib,json,sys
from pathlib import Path
names=json.load(sys.stdin)
print(json.dumps({name:hashlib.sha256((Path('/app')/name).read_bytes()).hexdigest() if (Path('/app')/name).is_file() else None for name in names}))"""
actual=json.loads(subprocess.check_output(['docker','exec','-i',WEB,'python','-c',code],input=json.dumps(list(expected)).encode()))
assert actual==expected,[name for name in expected if actual.get(name)!=expected[name]]
save(OUT/'raw/runtime-file-hashes.json',actual)
static={str(path.relative_to(context/'dojo/static')):hashlib.sha256(path.read_bytes()).hexdigest() for path in (context/'dojo/static').rglob('*') if path.is_file()}
checks=[]
for name,digest in static.items():
    actual_digest=subprocess.check_output(['docker','exec','aspm-rc3-nginx-1','sha256sum','/usr/share/nginx/html/static/'+name],text=True).split()[0]
    checks.append({'path':name,'sha256':actual_digest,'equal':actual_digest==digest})
assert all(row['equal'] for row in checks)
save(OUT/'raw/static-file-hashes.json',checks)
dependency_code="import json,sys,importlib.metadata as m;print(json.dumps({'python':sys.version,'packages':{d.metadata['Name']:d.version for d in m.distributions()}}))"
deps={}
for variant,image in [('rc2','aspm-build:25fb63ae7b48'),('rc3',build['images']['app']['tag'])]:
    deps[variant]=json.loads(subprocess.check_output(['docker','run','--rm','--entrypoint','python',image,'-c',dependency_code],text=True))
assert deps['rc2']==deps['rc3']
save(OUT/'raw/dependencies.json',deps)
images={}
for kind,entry in build['images'].items():
    record=json.loads(subprocess.check_output(['docker','image','inspect',entry['tag']],text=True))[0]
    assert record['Id']==entry['id']
    images[kind]={key:record.get(key) for key in ['Id','RepoDigests','Descriptor']}
    images[kind]['revision']=record['Config']['Labels']['org.opencontainers.image.revision']
    assert images[kind]['revision']==build['source_sha']
    alias='aspm:1.0.1-rc3' if kind=='app' else 'aspm-nginx:1.0.1-rc3'
    prior=subprocess.run(['docker','image','inspect',alias],capture_output=True,text=True)
    if prior.returncode==0:
        assert json.loads(prior.stdout)[0]['Id']==entry['id'],'Preserve a different existing RC3 alias'
    else:run(['docker','tag',entry['tag'],alias])
    images[kind]['local_rc3_alias']=alias
runtime_code="""import json,sys
from pathlib import Path
from django.conf import settings
from django.db import connection
argv=Path('/proc/1/cmdline').read_bytes().decode().split('\\0')
allowed={'--processes','--threads','--listen','--max-requests','--max-worker-lifetime','--reload-on-rss','--harakiri','--buffer-size'}
flags={arg:argv[index+1] for index,arg in enumerate(argv[:-1]) if arg in allowed}
print('RUNTIME '+json.dumps({'database':connection.settings_dict['NAME'],'conn_max_age':connection.settings_dict['CONN_MAX_AGE'],'flags':flags,'middleware':settings.MIDDLEWARE,'task_hooks_loaded':'rc3_tasks' in sys.modules}))"""
text=subprocess.check_output(['docker','exec',WEB,'python','manage.py','shell','-c',runtime_code],text=True)
runtime=json.loads(next(line[8:] for line in text.splitlines() if line.startswith('RUNTIME ')))
assert runtime['database']=='aspm_rc3_validation' and runtime['task_hooks_loaded'] is False
assert not any('rc3_perf' in item for item in runtime['middleware'])
logs=subprocess.run(['docker','logs',WEB],capture_output=True,text=True,check=True)
startup=[line for line in (logs.stdout+logs.stderr).splitlines() if any(word in line.lower() for word in ['listen backlog','spawned uwsgi worker','processes','threads'])]
runtime['startup_evidence']=startup
save(OUT/'raw/runtime-final.json',runtime)
connection=http.client.HTTPConnection('127.0.0.1',48092,timeout=30)
connection.request('GET','/login?force_login_form')
response=connection.getresponse();response.read()
assert response.status==200 and response.getheader('X-Perf-SQL-Count') is None
connection.close()
save(OUT/'raw/provenance.json',{'source_sha':build['source_sha'],'app_files_verified':len(expected),'static_files_verified':len(static),'dependencies_equal':True,'images':images,'measurement_middleware_removed':True,'task_hooks_removed':True,'stable_published':False,'registry_push':False})
# Restore the retained RC2 demo after all measurements; its worker must be scoped to validation.
records=json.loads(subprocess.check_output(['docker','inspect','aspm-rc2-aspm-1','aspm-rc2-worker-1'],text=True))
for record in records:
    env=dict(item.split('=',1) for item in record['Config']['Env'])
    assert urlsplit(env['DD_DATABASE_URL']).path=='/aspm_rc2_validation','Do not start a worker over source/seed'
run(['docker','start','aspm-rc2-aspm-1','aspm-rc2-worker-1','aspm-rc2-nginx-1'])
run(['docker','restart','aspm-rc2-nginx-1'])
save(OUT/'raw/demo-restored.json',{'rc2_port':48091,'rc3_port':48092,'rc2_database':'aspm_rc2_validation','rc3_database':'aspm_rc3_validation','source_worker_started':False})
print('Verified source files, dependencies, images, clean runtime and local RC3 aliases; retained demo restored')
