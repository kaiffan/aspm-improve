"""Correct diagnostic sort metadata; preserve the first profiles and all load runs."""
import copy
import json
import shutil
import subprocess
from common import OUT, PRIVATE, ROOT, WEB, app_config, compose, run, save, switch

assert (OUT/'raw/finalization-complete.json').exists()
archive=OUT/'diagnostics/prefetch-order-metadata'
archive.mkdir(parents=True,exist_ok=True)
for variant in ['round5','rc1','rc2']:
    for kind in ['profile','plans']:
        path=OUT/f'{kind}-{variant}.json'
        if not (archive/path.name).exists():shutil.copyfile(path,archive/path.name)
failed=OUT/'raw/report-controller.log'
if failed.exists() and not (archive/'failed-verification.txt').exists():shutil.copyfile(failed,archive/'failed-verification.txt')
(archive/'README.md').write_text('''# Diagnostic metadata correction

The first profile collector inferred Finding page ordering from the queryset rebuilt by `prefetch_for_findings`. That queryset holds an evaluated page cache and its model Meta.ordering no longer describes the actual page SELECT. The verification correctly refused to waive mismatched primary values.

The corrected collector uses the original `context["filtered"].qs` before pagination/prefetch. All104 diagnostic cases per build were recaptured on the same protected seed, with the worker stopped and the same credentials. These files preserve the first diagnostic attempt and its failed verification. No measured load observations, HTTP latency, SQL counts or actor schedule were edited. The105 load runs/17,100 measured requests are unchanged; final profiles/plans live two levels above this archive.
''')
with (PRIVATE/'profile-recapture.log').open('w') as log:
    compose('stop','worker',stdout=log,stderr=log)
    credentials=(PRIVATE/'accounts.json').read_bytes()
    try:
        for variant in ['round5','rc1','rc2']:
            switch(variant,prefix='rc2-sort-corrected-'+variant)
            run(['docker','cp',str(OUT/'scripts/profile.py'),WEB+':/tmp/rc2-profile.py'],stdout=log,stderr=log)
            run(['docker','cp',str(ROOT/'perf-report/round5/scenarios.json'),WEB+':/tmp/r4-scenarios.json'],stdout=log,stderr=log)
            result=run(['docker','exec','-i','-e','DD_FINAL_VARIANT='+variant,WEB,'python','manage.py','shell','-c',"exec(open('/tmp/rc2-profile.py').read())"],input=credentials,stdout=subprocess.PIPE,stderr=log)
            lines=result.stdout.decode().splitlines()
            save(OUT/f'profile-{variant}.json',[json.loads(x[8:]) for x in lines if x.startswith('PROFILE ')])
            save(OUT/f'plans-{variant}.json',[json.loads(x[5:]) for x in lines if x.startswith('PLAN ')])
            print('Corrected diagnostic profile',variant,flush=True)
    finally:
        switch('rc2','aspm_rc2_validation',False,'rc2-demo-final')
        config=json.loads((PRIVATE/'compose.json').read_text())
        worker=copy.deepcopy(config['services']['aspm'])
        worker['entrypoint']=['/entrypoint-celery-worker.sh']
        worker['environment'].update(DD_CELERY_WORKER_POOL_TYPE='prefork',DD_CELERY_WORKER_PREFETCH_MULTIPLIER='1',DD_CELERY_WORKER_CONCURRENCY='1',DD_CELERY_WORKER_AUTOSCALE_MIN='1',DD_CELERY_WORKER_AUTOSCALE_MAX='1')
        config['services']['worker']=worker
        save(PRIVATE/'compose.json',config,private=True)
        compose('up','-d','worker',stdout=log,stderr=log)
save(OUT/'raw/profile-correction.json',{'complete':True,'diagnostic_cases_per_build':104,'load_observations_unchanged':True,'archive':'diagnostics/prefetch-order-metadata'})
