"""Final integrity, complete JSON comparisons and release-gate evidence."""
import hashlib
import http.client
import io
import json
import subprocess
import tarfile
import time
from common import OUT, PRIVATE, ROOT, SOURCE, VARIANTS, WEB, output, pg, run, save

while not (OUT/'raw/finalization-complete.json').exists():time.sleep(10)
comparisons=[];differences=[]
left=json.loads((OUT/'profile-round5.json').read_text())
assert len(left)==104
for variant in ['rc1','rc2']:
    right={(x['actor'],x['case']):x for x in json.loads((OUT/f'profile-{variant}.json').read_text())}
    assert len(right)==104
    for x in left:
        y=right[x['actor'],x['case']]
        expected_status=403 if x['actor']!='admin' and x['case'] in ['users','notes'] else 200
        item={'variant':variant,'actor':x['actor'],'case':x['case'],'expected_status':expected_status,'status_before':x['status'],'status_after':y['status'],'status_equal':x['status']==y['status']==expected_status}
        if 'payload_hash' in x:
            item.update(json_equal=x['payload_hash']==y['payload_hash'],count_equal=x.get('count')==y.get('count'),order_equal=x.get('ids')==y.get('ids'),bytes_equal=x['bytes']==y['bytes'])
        elif x['case'] in ['simple_metrics','simple_metrics_cold']:
            item['numeric_cells_equal']=x['metrics_cells']==y['metrics_cells']
            if x['case']=='simple_metrics_cold':item['context_equal']=x['semantic']==y['semantic']
        else:
            a=dict(x.get('semantic',{}));b=dict(y.get('semantic',{}))
            # A stable PK intentionally resolves previously unspecified UI ties.
            for key in [k for k in a if k.endswith('_ids')]:
                if a[key]!=b.get(key):
                    prefix=key[:-len('_ids')]
                    assert a.get(prefix+'_sort_fields'), 'Do not waive a unique/unknown ordering difference'
                    assert a[prefix+'_sort_fields']==b.get(prefix+'_sort_fields') and a[prefix+'_sort_values']==b.get(prefix+'_sort_values'), 'Primary UI order changed'
                    differences.append({'variant':variant,'actor':x['actor'],'case':x['case'],'field':key,'reason':'Documented UI tie ordering; compare counts and stable pagination separately','before':a[key],'after':b.get(key)})
                del a[key];b.pop(key,None)
            item['context_equal']=a==b
        comparisons.append(item)
failures=[x for x in comparisons if not all(v for k,v in x.items() if k.endswith('_equal'))]
save(OUT/'compatibility.json',{'pairs':len(comparisons),'complete_json_pairs':sum('json_equal' in x for x in comparisons),'expected_denial_pairs':sum(x['expected_status']==403 for x in comparisons),'failures':failures,'documented_ui_tie_differences':differences,'comparisons':comparisons})
assert not failures
source_checks={}
verify_code="""import hashlib,json,sys
from pathlib import Path
data=json.load(sys.stdin);bad=[]
for name,wanted in data.items():
 p=Path('/app')/name
 try:actual={'link':str(p.readlink())} if isinstance(wanted,dict) else hashlib.sha256(p.read_bytes()).hexdigest()
 except OSError:actual=None
 if actual!=wanted:bad.append(name)
print(json.dumps({'checked':len(data),'mismatches':bad}))
"""
for variant,(tag,_,sha) in VARIANTS.items():
    expected={}
    with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',sha,'dojo'],cwd=ROOT))) as archive:
        for member in archive:
            if member.isfile():expected[member.name]=hashlib.sha256(archive.extractfile(member).read()).hexdigest()
            elif member.issym():expected[member.name]={'link':member.linkname}
    actual=json.loads(subprocess.check_output(['docker','run','--rm','--network','none','--entrypoint','python','-i',tag,'-c',verify_code],input=json.dumps(expected).encode()))
    assert not actual['mismatches']
    actual['source_sha']=sha;source_checks[variant]=actual
save(OUT/'raw/all-image-source-verification.json',source_checks)
from collections import Counter, defaultdict
schedule=defaultdict(dict)
for file in (OUT/'raw').glob('mixed-r*-*-c*-mixed.json'):
    row=json.loads(file.read_text())
    schedule[row['rep'],row['concurrency']][row['variant']]=Counter((x['case'],x['actor']) for x in row['samples'])
assert len(schedule)==15 and all(set(rows)==set(VARIANTS) and rows['round5']==rows['rc1']==rows['rc2'] for rows in schedule.values())
save(OUT/'raw/schedule-verification.json',{'groups':len(schedule),'all_actor_case_distributions_equal':True,'fixed_seeds':[35101,35102,35103],'accounts':25,'think_time':0})
sql="""SELECT json_build_object('findings',count(*),'sum_ids',sum(id)::text,
'rows_xor',bit_xor(hashtextextended(f::text,0))::text,'max_updated',max(updated),
'deduplication',(SELECT enable_deduplication FROM dojo_system_settings ORDER BY id LIMIT 1)) FROM dojo_finding f"""
data={db:json.loads(pg(sql,db)) for db in ['source','dd_round4_seed','aspm_rc2_validation']}
before=json.loads((OUT/'raw/dataset-before.json').read_text())
for db in ['source','dd_round4_seed']:
    assert all(data[db][key]==before[db][key] for key in ['findings','sum_ids','rows_xor','max_updated','deduplication'])
original=json.loads(pg(sql+' WHERE id<=1000168','aspm_rc2_validation'))
assert all(original[k]==data['source'][k] for k in ['findings','sum_ids','rows_xor','max_updated','deduplication'])
save(OUT/'raw/dataset-final.json',{'databases':data,'validation_original_prefix':original,'source_and_seed_unchanged':True,'validation_original_prefix_unchanged':True})
queue=int(output(['docker','exec','aspm-rc2-rc2-cache-1','valkey-cli','-n','0','LLEN','celery']))
assert queue==0
containers={}
for name in [WEB,'aspm-rc2-nginx-1','aspm-rc2-worker-1','aspm-rc2-rc2-cache-1','django-defectdojo-postgres-1']:
    d=json.loads(output(['docker','inspect',name]))[0]
    containers[name]={'image_id':d['Image'],'running':d['State']['Running'],'oom_killed':d['State']['OOMKilled']}
    assert d['State']['Running'] and not d['State']['OOMKilled']
assert containers[WEB]['image_id']==json.loads((OUT/'build.json').read_text())['variants']['rc2']['app']['id']
accounts=json.loads((PRIVATE/'accounts-copy.json').read_text())
conn=http.client.HTTPConnection('127.0.0.1',48091,timeout=20)
conn.request('GET','/api/v2/findings/?limit=1',headers={'Authorization':'Token '+accounts[0]['token']})
response=conn.getresponse();response.read();assert response.status==200 and response.getheader('X-Perf-SQL-Count') is None;conn.close()
login=json.loads((PRIVATE/'login.json').read_text());permission_checks=[]
for path in [f'/api/v2/findings/?test__engagement__product={accounts[0]["product"]}&limit=100',f'/api/v2/findings/?test__engagement__product={accounts[0]["product"]}&offset=500000&fast_offset=1',f'/api/v2/findings/?test__engagement__product={accounts[0]["product"]}&o=-title']:
    conn=http.client.HTTPConnection('127.0.0.1',48091,timeout=20);conn.request('GET',path,headers={'Authorization':'Token '+login['token']});response=conn.getresponse();payload=json.loads(response.read());conn.close()
    assert response.status==200 and payload['count']==0 and payload['results']==[]
    permission_checks.append({'path':path,'status':response.status,'count':0})
save(OUT/'raw/permission-checks.json',{'access_free_filtered_and_fast':permission_checks})
availability=json.loads(output(['docker','run','--rm','--network','none','--entrypoint','python','aspm-rc2-tests:25fb63ae7b48','-c',"import importlib.util,json,shutil; print(json.dumps({'selenium':importlib.util.find_spec('selenium') is not None,'chromedriver':shutil.which('chromedriver'),'chromium':shutil.which('chromium')}))"]))
save(OUT/'raw/legacy-selenium-availability.json',availability)
log_counts={}
for name in [WEB,'aspm-rc2-worker-1']:
    result=subprocess.run(['docker','logs','--since','30m',name],capture_output=True,text=True)
    text=result.stdout+result.stderr
    log_counts[name]={'tracebacks':text.count('Traceback (most recent call last)'), 'error_lines':sum(' ERROR ' in line for line in text.splitlines())}
    (PRIVATE/(name+'-final.log')).write_text(text)
assert all(x['tracebacks']==0 and x['error_lines']==0 for x in log_counts.values())
save(OUT/'raw/stand-final.json',{'source_sha':SOURCE,'containers':containers,'celery_queue':queue,'performance_middleware_removed':True,'log_counts':log_counts,'stable_published':False,'rc2_release_alias_promoted':False})
save(OUT/'raw/verification-complete.json',{'complete':True,'source_sha':SOURCE,'pairs':len(comparisons),'main_findings':data['source']['findings']})
print('Verified complete JSON/semantic comparisons:',len(comparisons),'main findings:',data['source']['findings'],flush=True)
