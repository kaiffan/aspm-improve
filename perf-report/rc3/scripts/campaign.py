"""Sequential paired tests only; never overlap load with full suites or builds."""
import json
from lab import OUT, ROOT, PRIVATE, WEB, run, save, switch, benchmark, fingerprint, audit

tests=json.loads((OUT/'raw/full-final-tests.json').read_text())
assert tests['wrapper_exit_code']==tests['errors']==tests['assertion_failures']==0
assert tests['skipped']==553
assert (OUT/'raw/build-final.json').exists()
assert not any((OUT/'raw').glob('campaign-*-mixed.json')), 'Existing campaign is preserved'
switch('rc2')
audit()
fingerprint('before-load')

# Isolate the incremental cost/benefit of Dashboard and UI on top of fix1.
for repeat in range(1,4):
    order=['fix1','rc3'] if repeat % 2 else ['rc3','fix1']
    for variant in order:
        switch(variant)
        benchmark(variant,25,repeat,phase='incremental')

# Main A/B series. Same generator, weights, actors, seeds, limits and bytes.
for repeat in range(1,4):
    for variant in (['rc2','rc3'] if repeat % 2 else ['rc3','rc2']):
        switch(variant)
        for concurrency in [1,5,10,15,25]:
            benchmark(variant,concurrency,repeat)

cases=['findings','filtered_product','finding_detail','products','tests','engagements',
       'dashboard','web_products','endpoints','web_findings','web_test']
for variant in ['rc3','rc2']:
    switch(variant)
    for case in cases:
        benchmark(variant,1,1,case,160,'endpoints')
switch('fix1')
for case in ['web_findings','web_test']:
    benchmark('fix1',1,1,case,160,'endpoints')

for variant in ['rc2','rc3']:
    switch(variant)
    run(['docker','cp',str(OUT/'scripts/profile.py'),WEB+':/tmp/rc3-profile.py'])
    run(['docker','cp',str(ROOT/'perf-report/round5/scenarios.json'),WEB+':/tmp/r4-scenarios.json'])
    with (OUT/'raw'/f'profile-final-{variant}.log').open('wb') as log:
        run(['docker','exec','-i','-e','DD_FINAL_VARIANT='+variant,WEB,'python','manage.py','shell','-c',"exec(open('/tmp/rc3-profile.py').read())"],input=(PRIVATE/'accounts.json').read_bytes(),stdout=log,stderr=log)
    lines=(OUT/'raw'/f'profile-final-{variant}.log').read_text().splitlines()
    for kind in ['PROFILE','SQL','PLAN']:
        save(OUT/'raw'/f'{kind.lower()}-final-{variant}.json',[json.loads(line[len(kind)+1:]) for line in lines if line.startswith(kind+' ')])
    print('PROFILES',variant,flush=True)
fingerprint('after-load')
save(OUT/'raw/campaign-complete.json',{'complete':True,'main_runs':30,'incremental_runs':6,'endpoint_runs':24,'measured_requests':14640})
print('CAMPAIGN COMPLETE',flush=True)
