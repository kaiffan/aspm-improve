#!/usr/bin/env python3
"""Controlled import/reimport on existing identical Round 4 DB copies only."""
import argparse
import datetime
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlsplit, urlunsplit

ROOT=Path(__file__).resolve().parent
WEB='dd-final-web-1'
PG='django-defectdojo-postgres-1'


def run(argv, **kwargs):
    return subprocess.run(argv, check=True, **kwargs)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compose',type=Path,required=True)
    parser.add_argument('--runtime-env',type=Path,required=True)
    parser.add_argument('--credentials',type=Path,required=True)
    parser.add_argument('--private-dir',type=Path,required=True)
    parser.add_argument('--stop-file',type=Path,required=True)
    parser.add_argument('--variants',default='original,current,final')
    parser.add_argument('--db-prefix',default='dd_round4_')
    parser.add_argument('--media-prefix',default='dd-final-bg-media-')
    parser.add_argument('--redis-offset',type=int,default=0)
    args=parser.parse_args()
    if args.stop_file.exists():parser.error('Stop file exists; inspect previous run first')
    private=args.private_dir
    raw=ROOT/'raw'
    credentials=json.loads(args.credentials.read_text())
    runtime=dict(line.split('=',1) for line in args.runtime_env.read_text().splitlines() if '=' in line and not line.startswith('#'))
    database_url=urlsplit(runtime['DD_DATABASE_URL'].strip('\"\''))
    settings_dir=private/'bg_settings';settings_dir.mkdir(exist_ok=True)
    (settings_dir/'local_settings.py').write_text('import os\nMIDDLEWARE=["perf_instrument.SQLMiddleware", *MIDDLEWARE]\nCACHES["default"]["KEY_PREFIX"]=os.environ["DD_FINAL_CACHE_PREFIX"]\nimport perf_bg_instrument\n')
    config=json.loads(args.compose.read_text())
    web=config['services']['web']
    web['environment'].update(DD_DATABASE_URL='${DD_FINAL_DATABASE_URL}',DD_CELERY_BROKER_URL='${DD_FINAL_BROKER_URL}')
    web['volumes']=[v for v in web['volumes'] if not v.endswith(':/app/media:ro') and not v.endswith(':/app/docker/extra_settings:ro')]
    web['volumes'] += ['bg_media:/app/media',str(settings_dir)+':/app/docker/extra_settings:ro',str(ROOT/'perf_bg_instrument.py')+':/app/perf_bg_instrument.py:ro']
    config['services']['bg-valkey']={'image':'dd-api-perf-valkey:local','pull_policy':'never'}
    config['services']['worker']={'image':'${DD_FINAL_IMAGE}','pull_policy':'never','env_file':web['env_file'],'environment':web['environment'].copy(),'entrypoint':['sh','-c','cp /app/docker/extra_settings/* /app/dojo/settings/ && exec python /app/background_worker.py'],'volumes':web['volumes']+[str(ROOT/'background_worker.py')+':/app/background_worker.py:ro']}
    config['volumes']['bg_media']={'external':True,'name':'${DD_FINAL_MEDIA}'}
    compose=private/'bg-compose.json';compose.write_text(json.dumps(config,indent=2));compose.chmod(0o600)
    with (raw/'background-controller.log').open('a',buffering=1) as log:
        for index,variant in enumerate(args.variants.split(',')):
            if variant not in ('original','current','final'):raise ValueError('Unknown build')
            database=args.db_prefix+variant
            if not database.startswith('dd_round4') or not database.replace('_','').isalnum():raise ValueError('Unsafe database name')
            env=os.environ.copy()
            env.update(DD_FINAL_IMAGE='dd-final-'+variant+':3.5.100',DD_FINAL_DATABASE_URL=urlunsplit(database_url._replace(path='/'+database)),DD_FINAL_BROKER_URL=f'redis://bg-valkey:6379/{args.redis_offset+index*2}',DD_FINAL_CACHE_PREFIX=f'dd-r4-bg-{variant}-{time.time_ns()}',DD_FINAL_MEDIA=args.media_prefix+variant)
            # This mutation is confined to the named copy, before either web or worker connects.
            sql='UPDATE dojo_system_settings SET enable_deduplication=true; SELECT NOT (enable_mail_notifications OR enable_jira OR enable_slack_notifications OR enable_msteams_notifications OR enable_webhooks_notifications OR enable_github) FROM dojo_system_settings;'
            output=subprocess.check_output(['docker','exec','-e','R4_DB='+database,'-e','R4_SQL='+sql,PG,'sh','-c','psql -X -U "$POSTGRES_USER" -d "$R4_DB" -Atc "$R4_SQL"'],text=True)
            if not output.strip().endswith('t'):raise RuntimeError('External integrations must be disabled in the controlled copy')
            volume=env['DD_FINAL_MEDIA']
            run(['docker','volume','create',volume],stdout=log,stderr=log)
            run(['docker','run','--rm','--entrypoint','sh','-v','django-defectdojo_defectdojo_media:/source:ro','-v',volume+':/target','dd-api-perf-valkey:local','-c','cp -a /source/. /target/ && chown -R 1001:1001 /target'],stdout=log,stderr=log)
            base=['docker','compose','-p','dd-final','-f',str(compose)]
            run(base+['up','-d','bg-valkey','worker','web'],env=env,stdout=log,stderr=log)
            run(base+['restart','nginx'],env=env,stdout=log,stderr=log)
            begin=time.time();deadline=time.monotonic()+90
            while time.monotonic()<deadline:
                try:
                    connection=http.client.HTTPConnection('127.0.0.1',48084,timeout=3)
                    connection.request('GET','/api/v2/findings/1000000/',headers={'Authorization':'Token '+credentials[0]['token']})
                    response=connection.getresponse();response.read();connection.close()
                    worker_logs=subprocess.check_output(['docker','logs','dd-final-worker-1'],text=True,stderr=subprocess.STDOUT)
                    if response.status==200 and '"event": "ready"' in worker_logs:break
                except (OSError,http.client.HTTPException,subprocess.SubprocessError):pass
                time.sleep(1)
            else:raise RuntimeError('Background stack not ready')
            context_code="from dojo.models import Product,Finding,System_Settings;from django.db import connection;import json;p=Product.objects.select_related('prod_type').get(pk=2);print('CONTEXT '+json.dumps({'product_name':p.name,'product_type_name':p.prod_type.name,'database':connection.settings_dict['NAME'],'findings_count':Finding.objects.count(),'product_findings':Finding.objects.filter(test__engagement__product_id=2).count(),'deduplication':System_Settings.objects.first().enable_deduplication}))"
            output=subprocess.check_output(['docker','exec',WEB,'python','manage.py','shell','-c',context_code],text=True,stderr=subprocess.DEVNULL)
            context=json.loads(next(line[8:] for line in output.splitlines() if line.startswith('CONTEXT ')))
            assert context['database']==database and context['findings_count']==1000168 and context['deduplication']
            stats_sql="SELECT count(*) FROM pg_stats WHERE schemaname='public' AND tablename='dojo_finding'"
            stats=int(subprocess.check_output(['docker','exec','-e','R4_DB='+database,'-e','R4_SQL='+stats_sql,PG,'sh','-c','psql -X -U "$POSTGRES_USER" -d "$R4_DB" -Atc "$R4_SQL"'],text=True).strip())
            assert stats>0,'Missing planner statistics in controlled copy'

            manifest_path=ROOT/'background_manifest.json'
            manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else []
            manifest.append({'variant':variant,'database':database,'initial_findings':context['findings_count'],'large_product_findings':context['product_findings'],'worker_concurrency':1,'finding_column_stats':stats,'deduplication':True,'image_id':subprocess.check_output(['docker','inspect','--format','{{.Image}}',WEB],text=True).strip()})
            manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
            accounts=[{**row,**context} if i==0 else row for i,row in enumerate(credentials)]
            stdin=json.dumps(accounts).encode()
            monitor_env=os.environ.copy();monitor_env.update(DD_FINAL_DB=database,DD_FINAL_VALKEY='dd-final-bg-valkey-1',DD_FINAL_REDIS_DB=str(args.redis_offset+index*2),DD_FINAL_WORKER='dd-final-worker-1')
            monitor=subprocess.Popen([sys.executable,str(ROOT/'monitor.py'),str(raw/f'background-{variant}-metrics.jsonl'),str(args.stop_file),'1200',WEB],env=monitor_env,stdout=log,stderr=log)
            run(['docker','exec',WEB,'python','-c',"from pathlib import Path; Path('/tmp/dd-r4-rss-stop').unlink(missing_ok=True)"],stdout=log,stderr=log)
            rss_log=(raw/f'background-{variant}-rss.jsonl').open('wb')
            rss=subprocess.Popen(['docker','exec','-i','-e','DD_RSS_DURATION=1200',WEB,'python','-'],stdin=subprocess.PIPE,stdout=rss_log,stderr=log)
            rss.stdin.write((ROOT/'worker_rss.py').read_bytes());rss.stdin.close()

            try:
                print('BACKGROUND '+variant+' idle',flush=True)
                run([sys.executable,str(ROOT/'import_scan.py'),'idle',str(raw/f'import-{variant}-idle.json')],input=stdin,stdout=log,stderr=log)
                def read_case(label,requests=600):
                    return [sys.executable,str(ROOT/'benchmark.py'),'--variant',variant,'--scenario','mixed','--concurrency','10','--requests',str(requests),'--warmup','0','--seconds','300','--timeout','90','--seed','35103','--stop-file',str(args.stop_file),'--output',str(raw/f'background-{variant}-{label}.json')]
                run(read_case('warmup-control',40),input=stdin,stdout=log,stderr=log)
                run(read_case('control'),input=stdin,stdout=log,stderr=log)
                run(read_case('warmup-loaded',40),input=stdin,stdout=log,stderr=log)
                read=subprocess.Popen(read_case('loaded'),stdin=subprocess.PIPE,stdout=log,stderr=log)
                read.stdin.write(stdin);read.stdin.close()
                time.sleep(1)
                print('BACKGROUND '+variant+' loaded',flush=True)
                run([sys.executable,str(ROOT/'import_scan.py'),'loaded',str(raw/f'import-{variant}-loaded.json')],input=stdin,stdout=log,stderr=log)
                if read.wait(timeout=320):raise RuntimeError('Read load failed')
                # Wait for any remaining notification/result callbacks before stopping this worker.
                for _ in range(30):
                    size=subprocess.check_output(['docker','exec','dd-final-bg-valkey-1','valkey-cli','-n',str(args.redis_offset+index*2),'LLEN','celery'],text=True).strip()
                    if size=='0':break
                    time.sleep(1)
                else:raise RuntimeError('Background queue did not drain')
                logs=subprocess.check_output(['docker','logs','--since',datetime.datetime.fromtimestamp(begin,datetime.UTC).isoformat(),'dd-final-worker-1'],text=True,stderr=subprocess.STDOUT)
                events=[]
                for line in logs.splitlines():
                    if 'R4_TASK ' in line:
                        events.append(json.loads(line.split('R4_TASK ',1)[1]))
                (ROOT/f'celery_{variant}.json').write_text(json.dumps(events,indent=2)+'\n')
                print('BACKGROUND '+variant+' complete: '+str(len(events))+' task events',flush=True)
            finally:
                run(['docker','exec',WEB,'touch','/tmp/dd-r4-rss-stop'],stdout=log,stderr=log)
                try:rss.wait(timeout=4)
                except subprocess.TimeoutExpired:rss.terminate()
                rss_log.close()
                monitor.terminate()
                try:monitor.wait(timeout=8)
                except subprocess.TimeoutExpired:monitor.kill()
                run(base+['stop','worker'],env=env,stdout=log,stderr=log)
            if args.stop_file.exists():raise RuntimeError('Resource guard stopped background test')


if __name__=='__main__':main()
