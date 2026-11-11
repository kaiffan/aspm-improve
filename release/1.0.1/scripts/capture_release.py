"""Safe allowlist of actual image, source, dependency and resource metadata."""
import datetime
import hashlib
import io
import json
import platform
import subprocess
import tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];repo=R.parents[1];m=json.loads((R/'measurements/build-rc.json').read_text())
def out(argv):return subprocess.check_output(argv,text=True).strip()
expected={}
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',m['source_sha'],'dojo'],cwd=repo))) as t:
 for e in t:
  if e.isfile():expected[e.name]=hashlib.sha256(t.extractfile(e).read()).hexdigest()
  elif e.issym():expected[e.name]={'link':e.linkname}
expected.update(m['compiled_translations'])
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
r=subprocess.run(['docker','exec','-i','aspm-rc1-aspm-1','python','-c',code],input=json.dumps(expected).encode(),stdout=subprocess.PIPE,check=True);verify=json.loads(r.stdout);verify['source_sha']=m['source_sha'];assert not verify['mismatches'];(R/'measurements/source-verification.json').write_text(json.dumps(verify,indent=2)+'\n')
code="""import json,platform,django,rest_framework,dojo
from django.conf import settings
from django.db import connection
from dojo.aspm.branding import get_branding
with connection.cursor() as c:
 pg={}
 for key in ('server_version','shared_buffers','work_mem','max_connections','max_parallel_workers_per_gather','shared_preload_libraries','block_size'):
  c.execute('SHOW '+key);pg[key]=c.fetchone()[0]
 c.execute(\"SELECT extversion FROM pg_extension WHERE extname='pg_stat_statements'\");extension=c.fetchone()
 c.execute('SELECT max(id) FROM dojo_finding');max_id=c.fetchone()[0]
print('RELEASE '+json.dumps({'brand':get_branding(),'upstream':dojo.__version__,'python':platform.python_version(),'django':django.get_version(),'drf':rest_framework.VERSION,'debug':settings.DEBUG,'database':connection.settings_dict['NAME'],'conn_max_age':connection.settings_dict['CONN_MAX_AGE'],'pg':pg,'pg_stat_statements':extension,'max_finding_id':max_id,'promotions_enabled':settings.ASPM_SHOW_UPSTREAM_PROMOTIONS}))
"""
s=out(['docker','exec','aspm-rc1-aspm-1','python','manage.py','shell','-c',code]);runtime=json.loads(next(x[8:] for x in s.splitlines() if x.startswith('RELEASE ')));assert runtime['debug'] is False and runtime['brand']['git_sha']==m['source_sha'] and runtime['database']=='aspm_rc1_validation'
limits={}
for name in ('aspm-rc1-aspm-1','django-defectdojo-postgres-1'):
 c=json.loads(out(['docker','inspect',name]))[0];limits[name]={k:c['HostConfig'].get(k) for k in ('Memory','NanoCpus','CpuQuota','PidsLimit')};limits[name]['oom_killed']=c['State']['OOMKilled'];limits[name]['image_id']=c['Image']
report={'captured_at':datetime.datetime.now(datetime.UTC).isoformat(),'host':{'platform':platform.platform(),'cpu':out(['sysctl','-n','machdep.cpu.brand_string']),'ram_bytes':int(out(['sysctl','-n','hw.memsize']))},'docker':json.loads(out(['docker','info','--format','{"cpus":{{.NCPU}},"memory_bytes":{{.MemTotal}},"version":"{{.ServerVersion}}"}'])),'power':out(['pmset','-g','batt']),'swap':out(['sysctl','-n','vm.swapusage']),'limits':limits,'runtime':runtime,'source_verification':verify}
(R/'measurements/environment.json').write_text(json.dumps(report,indent=2)+'\n');print('Verified production DEBUG=false, immutable source and safe runtime metadata')
