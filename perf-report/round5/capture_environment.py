"""Capture an explicit safe allowlist of runtime/resource metadata, never env secrets."""
import datetime
import json
import platform
import subprocess
from pathlib import Path
r=Path(__file__).resolve().parent
def call(argv):return subprocess.check_output(argv,text=True).strip()
row={'captured_at':datetime.datetime.now(datetime.UTC).isoformat(),'host':{'platform':platform.platform(),'cpu':call(['sysctl','-n','machdep.cpu.brand_string']),'ram_bytes':int(call(['sysctl','-n','hw.memsize']))},'docker':json.loads(call(['docker','info','--format','{"cpus":{{.NCPU}},"memory_bytes":{{.MemTotal}},"version":"{{.ServerVersion}}"}'])),'power':call(['pmset','-g','batt']),'power_configuration':call(['pmset','-g','custom']),'swap':call(['sysctl','-n','vm.swapusage']),'limits':{}}
for container in ['dd-r5-web-1','django-defectdojo-postgres-1']:
    i=json.loads(call(['docker','inspect',container]))[0];row['limits'][container]={k:i['HostConfig'].get(k) for k in ['Memory','NanoCpus','CpuPeriod','CpuQuota','PidsLimit']}
subprocess.run(['docker','cp',str(r.parent/'final/capture_config.py'),'dd-r5-web-1:/tmp/r5-config.py'],check=True,stdout=subprocess.DEVNULL)
out=call(['docker','exec','dd-r5-web-1','python','manage.py','shell','-c',"exec(open('/tmp/r5-config.py').read())"])
row['application']=json.loads(next(l[7:] for l in out.splitlines() if l.startswith('CONFIG ')))
sql="SELECT json_build_object('preload',current_setting('shared_preload_libraries'),'extension',(SELECT extversion FROM pg_extension WHERE extname='pg_stat_statements'),'database_bytes',pg_database_size(current_database()),'finding_heap',pg_relation_size('dojo_finding'),'finding_total',pg_total_relation_size('dojo_finding'))"
out=call(['docker','exec','-e','R5_SQL='+sql,'django-defectdojo-postgres-1','sh','-c','psql -X -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "$R5_SQL"'])
row['pg_diagnostics']=json.loads(out)
(r/'environment.json').write_text(json.dumps(row,indent=2)+'\n');print('Captured safe runtime/resource metadata')
