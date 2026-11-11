"""Run behavioral/performance guards only in the dedicated unit-test stack."""
import os
import re
import subprocess
from pathlib import Path
R=Path(__file__).resolve().parent
E=os.environ.copy();E.update(COMPOSE_FILE='/private/tmp/dd-35100-round5/test.compose.json',COMPOSE_PROJECT_NAME='dd-final-tests')
modules='unittests.test_round5_performance unittests.test_round4_performance unittests.test_dashboard unittests.test_api_product_prefetch unittests.test_api_finding_relation_filters unittests.test_api_finding_filter_no_multiply unittests.test_local_release_performance_checks unittests.test_apiv2_prefetch_test_finding_groups unittests.test_authorization_queries'
try:
    for image,label,tests,expected in [('dd-final-final-check:3.5.100','tests_red_final','unittests.test_round5_performance',1),('dd-r5-final-check:3.5.100','tests_final',modules,0)]:
        E['DD_FINAL_TEST_IMAGE']=image
        subprocess.run(['docker','compose','up','-d'],env=E,check=True)
        with (R/'raw'/f'{label}.log').open('w') as log:
            result=subprocess.run(['./run-unittest.sh','--test-case',tests],env=E,stdout=log,stderr=log)
        content=(R/'raw'/f'{label}.log').read_text()
        assert result.returncode==expected,(label,result.returncode)
        if expected:assert 'FAILED (failures=4)' in content and not re.search(r'^ERROR:',content,re.M)
        else:assert 'Ran 104 tests' in content and 'OK (skipped=8)' in content
        print(label,'verified',flush=True)
    with (R/'raw/checks_final.log').open('w') as log:
        for command in [['check'],['makemigrations','--check','--dry-run'],['spectacular','--file','/tmp/r5-schema.yml']]:
            subprocess.run(['docker','compose','exec','-T','uwsgi','python','manage.py',*command],env=E,stdout=log,stderr=log,check=True)
finally:
    subprocess.run(['docker','compose','stop'],env=E,check=True)
