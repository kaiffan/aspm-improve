"""Sanctioned wrapper on the retained, offline test volume; never the source DB."""
import argparse
import json
import os
import subprocess
from urllib.parse import urlsplit
from lab import ROOT, OUT, PRIVATE, RC2_PRIVATE, run, save

parser=argparse.ArgumentParser()
parser.add_argument('--labels',default='unittests')
parser.add_argument('--label',default='full-reproduced')
args=parser.parse_args()
config=json.loads((RC2_PRIVATE/'tests.compose.json').read_text())
app=config['services']['uwsgi']
database=urlsplit(app['environment']['DD_DATABASE_URL'])
assert database.hostname=='postgres', 'Only the offline test server is allowed'
assert all(service.get('networks')==['offline'] for service in config['services'].values())
assert config['networks']['offline']['internal'] is True
assert config['volumes']['tests-postgres']['name']=='dd-final-tests_check_postgres'
app['volumes']=[str(ROOT/path)+':/app/'+path+':ro' for path in ['dojo','components','docs','scripts','tests','unittests']]
app['volumes'].append(str(ROOT/'release/1.0.1/rc2/scripts/result_runner.py')+':/app/rc2_test_runner.py:ro')
save(PRIVATE/'tests.compose.json',config,True)
target=OUT/'raw'/(args.label+'-tests.json')
assert not target.exists(), 'Preserve existing test evidence'
command=['docker','compose','-p','rc3-tests','-f',str(PRIVATE/'tests.compose.json')]
with (PRIVATE/(args.label+'-tests.log')).open('w') as log:
    run([*command,'up','-d'],stdout=log,stderr=log)
    env={**os.environ,'COMPOSE_PROJECT_NAME':'rc3-tests','COMPOSE_FILE':str(PRIVATE/'tests.compose.json')}
    try:
        result=subprocess.run(['./run-unittest.sh','--test-case',args.labels],cwd=ROOT,env=env,stdout=log,stderr=log)
        run(['docker','cp','rc3-tests-uwsgi-1:/tmp/rc2-test-summary.json',str(target)],stdout=log,stderr=log)
    finally:
        run([*command,'stop'],stdout=log,stderr=log)
summary=json.loads(target.read_text())
summary.update(wrapper_exit_code=result.returncode,source_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
save(target,summary)
print({key:summary[key] for key in ['tests_run','passed','assertion_failures','errors','skipped']})
raise SystemExit(result.returncode)
