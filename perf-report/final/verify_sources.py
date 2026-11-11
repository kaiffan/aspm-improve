#!/usr/bin/env python3
"""Verify immutable image dojo files against source build contexts; capture safe metadata."""
import datetime
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
PRIVATE=Path(sys.argv[1])
SHAS={'original':'334bef02d65a74909fe976b22724526474d5a0f6','current':'20771ddc0bdfb4b763708f70e1cd6c131c3f6b5e','final':'70daa20757a9b5b99836343e50791a4de8c72fd0'}
code="""import hashlib,json;from pathlib import Path;p=Path('/app/dojo');print(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file() and not f.is_symlink() and '__pycache__' not in f.parts and f.suffix!='.pyc'}))"""
metadata={'captured_at':datetime.datetime.now(datetime.UTC).isoformat(),'source_commits':SHAS,'host':{'platform':platform.platform(),'machine':platform.machine(),'python':platform.python_version()},'images':{}}
for variant in SHAS:
    image='dd-final-'+variant+':3.5.100'
    info=json.loads(subprocess.check_output(['docker','image','inspect',image],text=True))[0]
    deployed=json.loads(subprocess.check_output(['docker','run','--rm','--entrypoint','python',image,'-c',code],text=True))
    source=PRIVATE/'build'/variant/'dojo'
    expected={str(f.relative_to(source)):hashlib.sha256(f.read_bytes()).hexdigest() for f in source.rglob('*') if f.is_file() and not f.is_symlink() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
    tracked = subprocess.check_output(['git','-c','core.quotePath=false','ls-tree','-r',SHAS[variant],'--','dojo'],cwd=ROOT.parents[1],text=True)
    for line in tracked.splitlines():
        info_line, name = line.split('\t',1)
        mode, kind, oid = info_line.split()
        if mode not in {'100644','100755'}:continue
        data=(PRIVATE/'build'/variant/name).read_bytes()
        actual_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert actual_blob==oid, variant+' Git blob mismatch: '+name

    assert deployed==expected,variant+' source mismatch'
    (ROOT/f'source_hashes_{variant}.json').write_text(json.dumps(deployed,sort_keys=True,indent=2)+'\n')
    metadata['images'][variant]={'id':info['Id'],'source_sha':SHAS[variant],'verified_files':len(deployed),'user':info['Config']['User']}
base=json.loads(subprocess.check_output(['docker','image','inspect','dd-api-perf-base:3.5.100'],text=True))[0]
metadata['common_runtime']={'id':base['Id'],'repo_digests':base.get('RepoDigests',[])}
metadata['docker']=json.loads(subprocess.check_output(['docker','info','--format','{"cpus":{{.NCPU}},"memory_bytes":{{.MemTotal}},"version":"{{.ServerVersion}}"}'],text=True))
for key,name in [('cpu','machdep.cpu.brand_string'),('ram_bytes','hw.memsize')]:
    metadata['host'][key]=subprocess.check_output(['sysctl','-n',name],text=True).strip()
metadata['power']=subprocess.check_output(['pmset','-g','batt'],text=True).strip()
metadata['power_configuration']=subprocess.check_output(['pmset','-g','custom'],text=True).strip()
limits={}
for container in ('dd-final-web-1','django-defectdojo-postgres-1'):
    info=json.loads(subprocess.check_output(['docker','inspect',container],text=True))[0]
    limits[container]={key:info['HostConfig'].get(key) for key in ('Memory','NanoCpus','CpuPeriod','CpuQuota','PidsLimit')}
metadata['limits']=limits
metadata['official_tag_verified']='334bef02d65a74909fe976b22724526474d5a0f6' in (ROOT/'official_tag_verification.txt').read_text()
(ROOT/'environment.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('Verified source files in all three immutable images and recorded environment')
