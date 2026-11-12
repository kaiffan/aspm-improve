"""Verify actual files, image identities and dependencies before measurement."""
import datetime
import hashlib
import io
import json
import platform
import subprocess
import tarfile
import tempfile
from pathlib import Path
from common import OUT, PRIVATE, ROOT, SOURCE, VARIANTS, WEB, output, pg, run, save

build=json.loads((OUT/'build-reproduced.json').read_text())
retained=json.loads((OUT/'build.json').read_text())
same={kind:build['images'][kind]['id']==retained['variants']['rc2'][kind]['id'] for kind in ['app','nginx']}
save(OUT/'raw/build-reproducibility.json',same)
assert all(same.values()), 'Repeated build identity differs from retained image'
expected={}
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'dojo'],cwd=ROOT))) as archive:
    for member in archive:
        if member.isfile(): expected[member.name]=hashlib.sha256(archive.extractfile(member).read()).hexdigest()
        elif member.issym(): expected[member.name]={'link':member.linkname}
expected.update(build['compiled_translations'])
code="""import hashlib,json,sys
from pathlib import Path
expected=json.load(sys.stdin);bad=[]
for name,wanted in expected.items():
 p=Path('/app')/name
 try:actual={'link':str(p.readlink())} if isinstance(wanted,dict) else hashlib.sha256(p.read_bytes()).hexdigest()
 except OSError:actual=None
 if actual!=wanted:bad.append(name)
print(json.dumps({'checked':len(expected),'mismatches':bad}))
"""
result=json.loads(subprocess.check_output(['docker','exec','-i',WEB,'python','-c',code],input=json.dumps(expected).encode()))
assert not result['mismatches']
result['source_sha']=SOURCE
save(OUT/'raw/source-verification.json',result)
static={k[len('dojo/static/'):]:v for k,v in expected.items() if k.startswith('dojo/static/') and isinstance(v,str)}
# Nginx images have no Python. Copy the small tracked static tree for hashing.
snapshot=Path(tempfile.mkdtemp(prefix='static-check-',dir=PRIVATE))/'dojo'
run(['docker','cp','aspm-rc2-nginx-1:/usr/share/nginx/html/static/dojo',str(snapshot)],stdout=subprocess.DEVNULL)
mismatches=[]
for name,wanted in static.items():
    if not name.startswith('dojo/'): continue
    path=snapshot/name[len('dojo/'):]
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=wanted:mismatches.append(name)
save(OUT/'raw/static-verification.json',{'checked':sum(k.startswith('dojo/') for k in static),'mismatches':mismatches})
assert not mismatches
packages={}
dependency_code="""import hashlib,importlib.metadata as m,json,platform
packages=sorted((d.metadata['Name'],d.version) for d in m.distributions())
print(json.dumps({'python':platform.python_version(),'packages':packages,'sha256':hashlib.sha256(json.dumps(packages).encode()).hexdigest()}))
"""
for variant,(tag,_,sha) in VARIANTS.items():
    packages[variant]=json.loads(output(['docker','run','--rm','--network','none','--entrypoint','python',tag,'-c',dependency_code]))
assert len({x['sha256'] for x in packages.values()})==1
save(OUT/'raw/dependencies.json',packages)
rc1_source=VARIANTS['rc1'][2]
rc1_head=output(['git','rev-parse','release/1.0.1-rc1'])
runtime_delta=output(['git','diff','--name-only',rc1_source+'..'+rc1_head,'--','dojo','components','requirements.txt','requirements-dev.txt','Dockerfile.django','Dockerfile.nginx'])
assert not runtime_delta
save(OUT/'raw/rc1-provenance.json',{'source_sha':rc1_source,'release_head':rc1_head,'runtime_paths_changed':runtime_delta.splitlines(),'all_changed_paths':output(['git','diff','--name-only',rc1_source+'..'+rc1_head]).splitlines()})
limits={}
for name in [WEB,'django-defectdojo-postgres-1']:
    d=json.loads(output(['docker','inspect',name]))[0]
    limits[name]={k:d['HostConfig'].get(k) for k in ['Memory','NanoCpus','CpuQuota','CpuPeriod','PidsLimit']}
    limits[name].update(image_id=d['Image'],oom_killed=d['State']['OOMKilled'])
settings={k:pg('SHOW '+k,'dd_round4_seed') for k in ['server_version','shared_buffers','work_mem','max_connections','max_parallel_workers_per_gather','shared_preload_libraries']}
settings['pg_stat_statements']=pg("SELECT extversion FROM pg_extension WHERE extname='pg_stat_statements'",'dd_round4_seed') or None
save(OUT/'raw/environment.json',{'captured_at':datetime.datetime.now(datetime.UTC).isoformat(),'host':platform.platform(),'cpu':output(['sysctl','-n','machdep.cpu.brand_string']),'ram_bytes':int(output(['sysctl','-n','hw.memsize'])),'docker':json.loads(output(['docker','info','--format','{"cpus":{{.NCPU}},"memory_bytes":{{.MemTotal}},"version":"{{.ServerVersion}}"}'])),'power':output(['pmset','-g','batt']),'limits':limits,'postgresql':settings,'uwsgi_processes':4,'uwsgi_threads':4})
save(OUT/'raw/preload-ready.json',{'source_sha':SOURCE,'reproducible_images':same,'runtime_files_verified':True,'dependencies_identical':True})
print('Immutable app/static images reproduced, source verified, dependencies identical',flush=True)
