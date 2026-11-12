"""Verify the complete accepted A/B cohort without selecting individual samples."""
import collections
import hashlib
import json
import subprocess
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]
raw=OUT/'raw'
build=json.loads((raw/'build-final.json').read_text())
tests=json.loads((raw/'full-final-tests.json').read_text())
assert tests['source_sha']==build['source_sha']
assert tests['errors']==tests['assertion_failures']==tests['wrapper_exit_code']==0
assert json.loads((raw/'campaign-complete.json').read_text())['complete']
generator_hashes={}
for name in ['benchmark.py','scenarios.json']:
    path='perf-report/round5/'+name
    baseline=subprocess.check_output(['git','show','9384826c2c2ccdbf0178ebc3faa5ea3e5513473d:'+path],cwd=OUT.parents[1])
    current=(OUT.parents[1]/path).read_bytes()
    assert current==baseline,'The original workload must remain unchanged'
    generator_hashes[path]=hashlib.sha256(current).hexdigest()
checks=[]
for repeat in [1,2,3]:
    for concurrency in [1,5,10,15,25]:
        runs={variant:json.loads((raw/f'campaign-{variant}-r{repeat}-c{concurrency}-mixed.json').read_text()) for variant in ['rc2','rc3']}
        expected={'findings':90,'filtered_product':45,'finding_detail':30,'products':30,'tests':30,'engagements':15,'dashboard':30,'web_products':15,'endpoints':15}
        for variant,run in runs.items():
            assert run['seed']==35100+repeat and run['concurrency']==concurrency
            assert run['configured_users']==25 and run['observed_users']==25
            assert run['requests']==len(run['samples'])==300 and not run['stopped']
            assert run['statuses']=={'200':300} and run['error_rate']==0
            assert collections.Counter(s['case'] for s in run['samples'])==expected
            assert all(s['sql_count'] is not None and s['sql_ms'] is not None for s in run['samples'])
            if variant=='rc3':assert run['image_id']==build['images']['app']['id']
        # The generator consumes a single seeded schedule. Completion order and
        # thread assignment may vary; compare the full actor/case/response sizes.
        schedules={variant:collections.Counter((s['actor'],s['case']) for s in run['samples']) for variant,run in runs.items()}
        assert schedules['rc2']==schedules['rc3'],(repeat,concurrency,'actor/case schedule differs')
        signatures={variant:collections.Counter((s['actor'],s['case'],s['bytes']) for s in run['samples'] if s['case'] not in ['dashboard','web_products']) for variant,run in runs.items()}
        assert signatures['rc2']==signatures['rc3'],(repeat,concurrency,'API response sizes differ')
        html_sizes=collections.defaultdict(list)
        for run in runs.values():
            for sample in run['samples']:
                if sample['case'] in ['dashboard','web_products']:html_sizes[sample['actor'],sample['case']].append(sample['bytes'])
        html_range=max(max(sizes)-min(sizes) for sizes in html_sizes.values())
        assert html_range<=2,'Investigate any HTML size difference beyond the observed timestamp formatting'
        checks.append({'repeat':repeat,'concurrency':concurrency,'requests_per_build':300,'weights_equal':True,'actor_case_schedule_equal':True,'api_response_sizes_equal':True,'html_max_size_range_bytes':html_range,'html_variation_reason':'Existing session_notify_time float in base.html; notifications/context_processors.py:session_expiry_notification. No response padding or payload reduction.','all_http_200':True})
summary={'source_sha':build['source_sha'],'pairs':len(checks),'main_requests':9000,'checks':checks,'generator':'Unmodified perf-report/round5/benchmark.py; warmup excluded','rc2_workload_file_hashes':generator_hashes}
(raw/'cohort-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print('Verified 15 main A/B pairs: exact mix/actors/API sizes; HTML timestamp variation <=2 bytes')
