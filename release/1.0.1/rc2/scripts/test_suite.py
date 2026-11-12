"""Sanctioned wrapper, isolated PostgreSQL, retained test volume, full discovery."""
import json
import os
import shutil
import subprocess
import time
from common import OUT, PRIVATE, ROOT, SOURCE, compose, run, save

records = {x['Name'].lstrip('/'): x for x in json.loads((PRIVATE/'containers.json').read_text())}
env = dict(x.split('=',1) for x in records['dd-final-tests-uwsgi-1']['Config']['Env'])
env = {k:v for k,v in env.items() if k.startswith('DD_')}
env['DD_TEST_RUNNER'] = 'rc2_test_runner.RecordRunner'
pg_env = dict(x.split('=',1) for x in records['dd-final-tests-postgres-1']['Config']['Env'])
pg_env = {k:v for k,v in pg_env.items() if k.startswith('POSTGRES_')}
config = {'services':{
    'postgres':{'image':'dd-api-perf-postgres:18.6','environment':pg_env,'volumes':['tests-postgres:/var/lib/postgresql'],'networks':['offline']},
    'valkey':{'image':'dd-api-perf-valkey:local','networks':['offline']},
    'uwsgi':{'image':'aspm-rc2-tests:25fb63ae7b48','entrypoint':['sleep','infinity'],'environment':env,
             'volumes':[str(ROOT/p)+':/app/'+p+':ro' for p in ['components','docs','scripts','tests','unittests']]+[str(OUT/'scripts/result_runner.py')+':/app/rc2_test_runner.py:ro'],
             'networks':['offline']}},
    'volumes':{'tests-postgres':{'external':True,'name':'dd-final-tests_check_postgres'}},
    'networks':{'offline':{'internal':True}}}
save(PRIVATE/'tests.compose.json',config,private=True)
with (PRIVATE/'full-tests.log').open('w') as log:
    compose('up','-d','postgres','valkey','uwsgi',test=True,stdout=log,stderr=log)
    for attempt in range(30):
        if subprocess.run(['docker','exec','dd-final-tests-postgres-1','pg_isready'],stdout=log,stderr=log).returncode==0:
            break
        time.sleep(1)
    else:
        raise RuntimeError('Isolated test PostgreSQL is not ready')
    test_env={**os.environ,'COMPOSE_FILE':str(PRIVATE/'tests.compose.json'),'COMPOSE_PROJECT_NAME':'dd-final-tests'}
    code=subprocess.run(['./run-unittest.sh','--test-case','unittests'],cwd=ROOT,env=test_env,stdout=log,stderr=log).returncode
    run(['docker','cp','dd-final-tests-uwsgi-1:/tmp/rc2-test-summary.json',str(OUT/'raw/full-test-summary.json')],stdout=log,stderr=log)
    compose('stop',test=True,stdout=log,stderr=log)
summary=json.loads((OUT/'raw/full-test-summary.json').read_text())
summary.update(source_sha=SOURCE,wrapper_exit_code=code)
save(OUT/'raw/full-test-summary.json',summary)
save(OUT/'raw/tests-complete.json',{'source_sha':SOURCE,'complete':True,'exit_code':code})
print(json.dumps({k:summary[k] for k in ['tests_run','passed','assertion_failures','errors','skipped','error_details']},indent=2),flush=True)
