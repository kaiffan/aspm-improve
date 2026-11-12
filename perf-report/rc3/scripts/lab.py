"""RC3 isolated lab. Credentials are read from an explicit private RC2 configuration.

No migration, volume deletion, source write, or database reset is performed.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'perf-report/rc3'
PRIVATE = Path(os.environ.get('RC3_PRIVATE', ROOT.parent / 'aspm-rc3-private'))
RC2_PRIVATE = Path(os.environ.get('RC2_PRIVATE', '/Users/nightmare/Documents/ChatGPT/defect_dojo_fork/.cache/aspm-rc2-private'))
PG = 'django-defectdojo-postgres-1'
WEB = 'aspm-rc3-aspm-1'
SOURCE = '25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb'


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def save(path, data, private=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    if private:
        path.chmod(0o600)


def pg(sql, database='source'):
    return subprocess.check_output(['docker', 'exec', '-e', 'RC3_SQL='+sql,
        '-e', 'RC3_DB'+'='+('' if database == 'source' else database), PG, 'sh', '-c',
        'PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=180000 -c TimeZone=UTC -c DateStyle=ISO,MDY" psql -X -U "$POSTGRES_USER" -d "${RC3_DB:-$POSTGRES_DB}" -Atc "$RC3_SQL"'], text=True).strip()


def fingerprint(label):
    sql = """SELECT json_build_object('count',count(*),'sum_ids',sum(id)::text,
    'full_row_xor',bit_xor(hashtextextended(f::text,0))::text,
    'max_updated',max(updated),'database',current_database()) FROM dojo_finding f"""
    data = {db:json.loads(pg(sql,db)) for db in ['source','dd_round4_seed']}
    assert data['source']['count'] == data['dd_round4_seed']['count'] == 1000168
    for key in ['count','sum_ids','full_row_xor','max_updated']:
        assert data['source'][key] == data['dd_round4_seed'][key], key
    for db in ['source','dd_round4_seed']:
        sql = "COPY (SELECT id, encode(sha256(convert_to(f::text,'UTF8')),'hex') FROM dojo_finding f ORDER BY id) TO STDOUT"
        process = subprocess.Popen(['docker','exec','-e','RC3_SQL='+sql,'-e','RC3_DB='+('' if db=='source' else db),PG,'sh','-c',
            'PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=180000 -c TimeZone=UTC -c DateStyle=ISO,MDY" psql -X -q -U "$POSTGRES_USER" -d "${RC3_DB:-$POSTGRES_DB}" -c "$RC3_SQL"'],stdout=subprocess.PIPE)
        digest=hashlib.sha256()
        for chunk in iter(lambda:process.stdout.read(1024*1024),b''):
            digest.update(chunk)
        assert process.wait()==0
        data[db]['sha256_of_ordered_row_sha256']=digest.hexdigest()
    assert data['source']['sha256_of_ordered_row_sha256']==data['dd_round4_seed']['sha256_of_ordered_row_sha256']
    save(OUT/'raw'/f'integrity-{label}.json', data)
    print('Integrity', label, data, flush=True)


def audit():
    records=json.loads(subprocess.check_output(['docker','inspect',WEB,'aspm-rc2-worker-1',PG],text=True))
    safe=[]
    for record in records:
        env=dict(item.split('=',1) for item in record['Config']['Env'])
        safe.append(dict(name=record['Name'],image_id=record['Image'],labels=record['Config'].get('Labels'),
            memory_limit=record['HostConfig']['Memory'],cpu_limit=record['HostConfig']['NanoCpus'],
            running=record['State']['Running'],oom_killed=record['State']['OOMKilled'],
            runtime_env={k:v for k,v in env.items() if k.startswith(('DD_UWSGI_','DD_CELERY_WORKER_'))}))
    settings_code="""import json,importlib.metadata as m
from django.conf import settings
print('AUDIT '+json.dumps(dict(debug=settings.DEBUG,conn_max_age=settings.DATABASES['default']['CONN_MAX_AGE'],database=settings.DATABASES['default']['NAME'],middleware=settings.MIDDLEWARE,dependencies={d.metadata['Name']:d.version for d in m.distributions()})))"""
    output=subprocess.check_output(['docker','exec',WEB,'python','manage.py','shell','-c',settings_code],text=True)
    settings=json.loads(next(line[6:] for line in output.splitlines() if line.startswith('AUDIT ')))
    names=['max_connections','shared_buffers','work_mem','effective_cache_size','random_page_cost','effective_io_concurrency','max_parallel_workers_per_gather','default_statistics_target','jit','track_io_timing','shared_preload_libraries','stats_fetch_consistency']
    sql="SELECT json_agg(x) FROM (SELECT name,setting,unit FROM pg_settings WHERE name IN ("+','.join("'"+n+"'" for n in names)+") ORDER BY name) x"
    result=dict(containers=safe,settings=settings,postgres_settings=json.loads(pg(sql,'dd_round4_seed')),
        docker=json.loads(subprocess.check_output(['docker','info','--format','{{json .}}'],text=True)),
        power=subprocess.check_output(['pmset','-g','batt'],text=True),
        swap=subprocess.check_output(['sysctl','-n','vm.swapusage'],text=True),
        pressure=subprocess.check_output(['memory_pressure','-Q'],text=True))
    # Docker info may contain registry configuration and host metadata; retain only resources/version.
    result['docker']={k:result['docker'][k] for k in ['NCPU','MemTotal','ServerVersion','Architecture','OperatingSystem']}
    save(OUT/'raw/environment.json',result)


def compose(*args, **kwargs):
    return run(['docker','compose','-p','aspm-rc3','-f',str(PRIVATE/'compose.json'),*args], **kwargs)


def ready():
    import http.client
    for _ in range(60):
        try:
            connection=http.client.HTTPConnection('127.0.0.1',48092,timeout=2)
            connection.request('GET','/login?force_login_form')
            response=connection.getresponse();response.read();connection.close()
            if response.status==200:return
        except (OSError,http.client.HTTPException):pass
        time.sleep(1)
    raise RuntimeError('Gateway not ready')


def setup():
    PRIVATE.mkdir(parents=True, exist_ok=True)
    PRIVATE.chmod(0o700)
    (OUT/'raw').mkdir(parents=True, exist_ok=True)
    for directory in ['instrumented','plain']:
        target = PRIVATE/directory
        target.mkdir(exist_ok=True)
        target.chmod(0o755)
        text = "import os\nEMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'\nCACHES['default']['KEY_PREFIX']=os.environ.get('DD_FINAL_CACHE_PREFIX','rc3')\n"
        if directory == 'instrumented':
            shutil.copyfile(ROOT/'perf-report/round5/perf_instrument.py',target/'rc3_perf.py')
            text += "import sys\nsys.path.insert(0,'/app/docker/extra_settings')\nMIDDLEWARE=['rc3_perf.SQLMiddleware',*MIDDLEWARE]\n"
        (target/'local_settings.py').write_text(text)
        for p in target.iterdir():
            p.chmod(0o644)
    shutil.copyfile(RC2_PRIVATE/'accounts.json',PRIVATE/'accounts.json')
    (PRIVATE/'accounts.json').chmod(0o600)
    shutil.copyfile(ROOT/'release/1.0.1/nginx.conf',PRIVATE/'nginx.conf')
    (PRIVATE/'nginx.conf').chmod(0o644)
    fingerprint('before')


def switch(variant):
    config = json.loads((RC2_PRIVATE/'base.compose.json').read_text())
    app = config['services']['aspm']
    env = app['environment']
    parsed = urlsplit(env['DD_DATABASE_URL'])
    env['DD_DATABASE_URL'] = urlunsplit(parsed._replace(path='/dd_round4_seed'))
    if os.environ.get('RC3_AUDIT_PG') == '1':
        credentials = parsed.netloc.rsplit('@',1)[0]
        env['DD_DATABASE_URL'] = urlunsplit(parsed._replace(netloc=credentials+'@rc3-sql-audit-postgres-1:5432',path='/dd_round4_seed'))
    env['DD_CELERY_BROKER_URL'] = 'redis://rc2-cache:6379/0'
    env['DD_CACHE_URL'] = 'redis://rc2-cache:6379/1'
    env['DD_FINAL_CACHE_PREFIX'] = 'rc3-'+variant
    env.pop('DD_ASPM_GIT_SHA',None)
    env.pop('DD_ASPM_BUILD_TIMESTAMP',None)
    manifests = {'fix1':'build-fix1.json','dashboard':'build-dashboard.json','rc3':'build-final.json'}
    manifest = json.loads((OUT/'raw'/manifests[variant]).read_text()) if variant != 'rc2' else None
    app['image'] = manifest['images']['app']['tag'] if manifest else 'aspm-build:25fb63ae7b48'
    if manifest:
        config['services']['nginx']['image'] = manifest['images']['nginx']['tag']
    app['volumes'] = ['media:/app/media:ro',str(PRIVATE/'instrumented')+':/app/docker/extra_settings:ro']
    config['services']['nginx']['ports'] = ['127.0.0.1:48092:8080']
    config['services']['nginx']['volumes'] = [str(PRIVATE/'nginx.conf')+':/tmp/aspm-nginx.conf:ro']
    save(PRIVATE/'compose.json',config,True)
    with (OUT/'raw/controller.log').open('a') as log:
        compose('up','-d','aspm','nginx','rc2-cache',stdout=log,stderr=log)
        compose('restart','nginx',stdout=log,stderr=log)
    import http.client
    for _ in range(60):
        try:
            conn=http.client.HTTPConnection('127.0.0.1',48092,timeout=2)
            conn.request('GET','/login?force_login_form')
            response=conn.getresponse()
            response.read()
            conn.close()
            if response.status == 200:
                actual = subprocess.check_output(['docker','inspect','--format','{{.Image}}',WEB],text=True).strip()
                expected = subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',app['image']],text=True).strip()
                assert actual == expected, 'Unexpected running image'
                return
        except (OSError,http.client.HTTPException):
            pass
        time.sleep(1)
    raise RuntimeError('Gateway not ready')


def benchmark(variant, concurrency, repeat, scenario='mixed', count=300, phase='campaign'):
    label=f'{phase}-{variant}-r{repeat}-c{concurrency}-{scenario}'
    target=OUT/'raw'/(label+'.json')
    if target.exists():
        raise RuntimeError('Preserving existing raw cohort: '+str(target))
    stop=PRIVATE/'resource-stop'
    if stop.exists():
        raise RuntimeError('Inspect resource-stop before proceeding')
    env={**os.environ,'DD_FINAL_DB':'dd_round4_seed','DD_FINAL_VALKEY':'aspm-rc3-rc2-cache-1','DD_FINAL_WORKER':'aspm-no-worker'}
    with (OUT/'raw/monitor.log').open('a') as log:
        monitor=subprocess.Popen([sys.executable,str(ROOT/'release/1.0.1/scripts/monitor_release.py'),str(OUT/'raw'/(label+'-metrics.jsonl')),str(stop),'1800',WEB],env=env,stdout=log,stderr=log)
        rss_file=(OUT/'raw'/(label+'-rss.jsonl')).open('wb')
        run(['docker','exec',WEB,'python','-c',"from pathlib import Path; Path('/tmp/dd-r4-rss-stop').unlink(missing_ok=True)"])
        rss=subprocess.Popen(['docker','exec','-i','-e','DD_RSS_DURATION=1800',WEB,'python','-'],stdin=subprocess.PIPE,stdout=rss_file,stderr=log)
        rss.stdin.write((ROOT/'perf-report/round5/worker_rss.py').read_bytes())
        rss.stdin.close()
        try:
            argv=[sys.executable,str(ROOT/'perf-report/round5/benchmark.py'),'--url','http://127.0.0.1:48092','--variant',variant,'--scenario',scenario,'--concurrency',str(concurrency),'--requests',str(count),'--warmup','25' if scenario=='mixed' else '5','--seconds','900','--timeout','90','--seed',str(35100+repeat),'--stop-file',str(stop),'--output',str(target)]
            run(argv,input=(PRIVATE/'accounts.json').read_bytes())
        finally:
            run(['docker','exec',WEB,'touch','/tmp/dd-r4-rss-stop'])
            try:
                rss.wait(timeout=3)
            except subprocess.TimeoutExpired:
                rss.terminate()
            rss_file.close()
            monitor.terminate()
            monitor.wait(timeout=8)
    data=json.loads(target.read_text())
    data.update(repeat=repeat,phase=phase,image_id=subprocess.check_output(['docker','inspect','--format','{{.Image}}',WEB],text=True).strip())
    save(target,data)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['setup','switch','benchmark','fingerprint'])
    parser.add_argument('--variant',default='rc2')
    parser.add_argument('--concurrency',type=int,default=25)
    parser.add_argument('--repeat',type=int,default=1)
    parser.add_argument('--scenario',default='mixed')
    parser.add_argument('--requests',type=int,default=300)
    parser.add_argument('--phase',default='campaign')
    args=parser.parse_args()
    if args.action=='setup': setup()
    elif args.action=='switch': switch(args.variant)
    elif args.action=='fingerprint': fingerprint(args.phase)
    else: benchmark(args.variant,args.concurrency,args.repeat,args.scenario,args.requests,args.phase)
