"""Separate CPU/allocation diagnostics from both exact final source images."""
import json
import shutil
from lab import ROOT,OUT,PRIVATE,WEB,run,save,switch

build=json.loads((OUT/'raw/build-final.json').read_text())
provenance=OUT/'raw/process-profile-provenance.json'
if provenance.exists() and json.loads(provenance.read_text())['rc3_source_sha']==build['source_sha']:
    raise SystemExit(0)
archive=OUT/'raw/pre-related-order-guard'
archive.mkdir(exist_ok=True)
for variant in ['rc2','rc3']:
    for suffix in ['json','log']:
        path=OUT/'raw'/f'process-{variant}.{suffix}'
        if path.exists():shutil.move(str(path),archive/path.name)
    switch(variant)
    run(['docker','cp',str(OUT/'scripts/process_profile.py'),WEB+':/tmp/process-profile.py'])
    run(['docker','cp',str(ROOT/'perf-report/round5/scenarios.json'),WEB+':/tmp/r4-scenarios.json'])
    with (OUT/'raw'/f'process-{variant}.log').open('wb') as log:
        run(['docker','exec','-i','-e','RC3_VARIANT='+variant,WEB,'python','manage.py','shell','-c',"exec(open('/tmp/process-profile.py').read())"],input=(PRIVATE/'accounts.json').read_bytes(),stdout=log,stderr=log)
    lines=(OUT/'raw'/f'process-{variant}.log').read_text().splitlines()
    save(OUT/'raw'/f'process-{variant}.json',[json.loads(line[7:]) for line in lines if line.startswith('MEMORY ')])
save(provenance,{'rc2_source_sha':'25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb','rc3_source_sha':build['source_sha'],'method':'Tracemalloc plus process CPU/RSS in a separate Django process; excluded from HTTP latency series'})
