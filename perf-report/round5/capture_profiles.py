import argparse,json,subprocess
from pathlib import Path
from types import SimpleNamespace
from run_suite import switch
p=argparse.ArgumentParser();p.add_argument('--variants',default='round4,round5');args=p.parse_args()
r=Path(__file__).resolve().parent;accounts=json.loads(Path('/private/tmp/dd-35100-round4/accounts.json').read_text())
with (r/'raw/phase-controller.log').open('a') as log:
 for v in args.variants.split(','):
  switch(v,SimpleNamespace(compose=Path('/private/tmp/dd-35100-round5/compose.json'),phase='phases'),accounts,log)
  subprocess.run(['docker','cp',str(r/'profile_phases.py'),'dd-r5-web-1:/tmp/r5-profile-phases.py'],check=True,stdout=log,stderr=log)
  out=subprocess.check_output(['docker','exec','-i','dd-r5-web-1','python','manage.py','shell','-c',"exec(open('/tmp/r5-profile-phases.py').read())"],input=json.dumps(accounts).encode(),stderr=log).decode()
  rows=[json.loads(l[8:]) for l in out.splitlines() if l.startswith('PROFILE ')];(r/f'phases_{v}.json').write_text(json.dumps(rows,indent=2)+'\n')
  print(v,[(x['actor'],x['case'],round(x['wall_ms']),round(x['sql_ms'])) for x in rows],flush=True)
