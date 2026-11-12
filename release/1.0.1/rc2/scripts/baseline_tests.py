"""Reproduce inherited discovery failures and prove the behavioral tests are red/green."""
import json
import os
import subprocess
import time
from common import OUT, PRIVATE, ROOT, SOURCE, compose, run, save

while not (OUT/'raw/tests-complete.json').exists():time.sleep(5)
path=PRIVATE/'tests.compose.json'
base=json.loads(path.read_text())
env={**os.environ,'COMPOSE_FILE':str(path),'COMPOSE_PROJECT_NAME':'dd-final-tests'}
results=[]


def execute(name, image, modules, old_fixture=False):
    config=json.loads(json.dumps(base))
    config['services']['uwsgi']['image']=image
    if old_fixture:
        original=PRIVATE/'original_tag_perf.py'
        original.write_bytes(subprocess.check_output(['git','show','release/1.0.1-rc1:unittests/test_tag_inheritance_perf.py'],cwd=ROOT))
        original.chmod(0o644)
        config['services']['uwsgi']['volumes'].append(str(original)+':/app/unittests/test_tag_inheritance_perf.py:ro')
    save(path,config,private=True)
    with (PRIVATE/(name+'.log')).open('w') as log:
        compose('up','-d','postgres','valkey','uwsgi',test=True,stdout=log,stderr=log)
        code=subprocess.run(['./run-unittest.sh','--test-case',modules],cwd=ROOT,env=env,stdout=log,stderr=log).returncode
        run(['docker','cp','dd-final-tests-uwsgi-1:/tmp/rc2-test-summary.json',str(OUT/'raw'/(name+'.json'))],stdout=log,stderr=log)
    summary=json.loads((OUT/'raw'/(name+'.json')).read_text())
    summary.update(wrapper_exit_code=code,image=image,old_fixture=old_fixture)
    save(OUT/'raw'/(name+'.json'),summary)
    results.append({'name':name,'run':summary['tests_run'],'passed':summary['passed'],'failures':summary['assertion_failures'],'errors':summary['errors'],'skipped':summary['skipped']})
    print(json.dumps(results[-1]),flush=True)
    return summary


try:
    for variant in ['round5','rc1']:
        data=execute('inherited-errors-'+variant,'aspm-rc2-test-baseline:'+variant,'unittests.test_ticket_comments unittests.tools.test_trufflehog_parser')
        assert data['errors']==2 and not data['assertion_failures']
    data=execute('pagination-red-rc1','aspm-rc2-test-baseline:rc1','unittests.test_ui_pagination_hardening unittests.test_finding_pagination_collections')
    assert data['errors']+data['assertion_failures']>0
    ordered='unittests.test_tag_inheritance unittests.test_tag_inheritance_perf.TagInheritanceImportPerfBaselines'
    data=execute('grade-cache-red-rc1','aspm-rc2-test-baseline:rc1',ordered,old_fixture=True)
    assert data['errors']+data['assertion_failures']>0
    data=execute('grade-cache-green-rc2','aspm-rc2-tests:25fb63ae7b48',ordered)
    assert data['errors']==data['assertion_failures']==0
finally:
    save(path,base,private=True)
    with (PRIVATE/'baseline-stop.log').open('w') as log:compose('stop',test=True,stdout=log,stderr=log)
save(OUT/'raw/baseline-tests-complete.json',{'complete':True,'source_sha':SOURCE,'runs':results})
