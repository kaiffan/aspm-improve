"""Verify Git blob identities in both immutable local images without printing image environment."""
# ruff: noqa: INP001, T201
import json
import subprocess
from pathlib import Path

BASE = '19cd7b4129de52e75eabaf0e07739e4c2b682f8e'
CANDIDATE = '12dfcbe6bb0beb1cbe0bd411b2c26b820cb9d23a'
checks = {}
code = '''import hashlib,json,pathlib,sys
expected=json.load(sys.stdin); mismatches=[]
for path,identity in expected.items():
 p=pathlib.Path('/app')/path
 data=str(p.readlink()).encode() if p.is_symlink() else p.read_bytes() if p.exists() else b'__MISSING__'
 actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\\0'+data).hexdigest()
 if actual!=identity: mismatches.append(path)
print(json.dumps({'checked_files':len(expected),'mismatches':mismatches,'passed':not mismatches}))
'''
for name, revision, image in [('A', BASE, 'aspm-rc5-api-integration:19cd7b4129de-qualified'), ('B', CANDIDATE, 'aspm-zero-finalize:12dfcbe6bb0b')]:
    lines = subprocess.check_output(['git','ls-tree','-r',revision,'dojo'],text=True).splitlines()
    expected = {line.split('\t',1)[1]: line.split()[2] for line in lines}
    result = subprocess.run(['docker','run','--rm','-i','--network','none','--cpus','.5','--memory','128m','--entrypoint','python',image,'-c',code], input=json.dumps(expected),text=True,capture_output=True,check=True)
    verification = json.loads(result.stdout)
    metadata = json.loads(subprocess.check_output(['docker','image','inspect',image]))[0]
    labels = metadata['Config'].get('Labels',{})
    assert labels['org.opencontainers.image.revision'] == revision
    assert verification['passed'], verification
    checks[name] = {'source_sha':revision,'image':image,'image_id':metadata['Id'],'architecture':metadata['Architecture'],'labels':labels,**verification}
Path('integration-report/zero-finalize-flow/checks/image-provenance.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps({name:{key:value[key] for key in ('source_sha','image_id','checked_files','passed')} for name,value in checks.items()}))
