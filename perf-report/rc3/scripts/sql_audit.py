"""pg_stat_statements on a streamed, isolated copy. Never restart/change source PG."""
import json
import os
import subprocess
import sys
import time
from urllib.parse import unquote, urlsplit
from lab import ROOT, OUT, PRIVATE, RC2_PRIVATE, PG, WEB, run, save, switch

assert json.loads((OUT/'raw/campaign-complete.json').read_text())['complete']
while (PRIVATE/'ui-filter-review-pending').exists():
    time.sleep(2)
assert not (OUT/'raw/sql-audit-complete.json').exists(), 'Existing audit is preserved'
base=json.loads((RC2_PRIVATE/'base.compose.json').read_text())
url=urlsplit(base['services']['aspm']['environment']['DD_DATABASE_URL'])
image=subprocess.check_output(['docker','inspect','--format','{{.Image}}',PG],text=True).strip()
config={'services':{'postgres':{'image':image,'environment':{
    'POSTGRES_USER':unquote(url.username),'POSTGRES_PASSWORD':unquote(url.password),'POSTGRES_DB':'dd_round4_seed'},
    'command':['postgres','-c','shared_preload_libraries=pg_stat_statements','-c','pg_stat_statements.track=all','-c','track_io_timing=on'],
    'volumes':['audit-data:/var/lib/postgresql'],'networks':['audit']}},
    'volumes':{'audit-data':{}},'networks':{'audit':{'external':True,'name':'aspm-rc3_default'}}}
save(PRIVATE/'sql-audit.compose.json',config,True)
command=['docker','compose','-p','rc3-sql-audit','-f',str(PRIVATE/'sql-audit.compose.json')]
AUDIT='rc3-sql-audit-postgres-1'
log=(PRIVATE/'sql-audit.log').open('a')
run([*command,'up','-d'],stdout=log,stderr=log)
for _ in range(60):
    if subprocess.run(['docker','exec',AUDIT,'pg_isready'],stdout=log,stderr=log).returncode==0:break
    time.sleep(1)
else:raise RuntimeError('Isolated audit PostgreSQL unavailable')


def sql(statement):
    return subprocess.check_output(['docker','exec','-e','RC3_SQL='+statement,AUDIT,'sh','-c',
        'psql -X -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "$RC3_SQL"'],text=True).strip()


existing=sql("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='dojo_finding'")
assert existing=='0', 'Do not overwrite an existing audit database'
# No dump is written to the worktree. Both streams stay within local Docker.
dump=subprocess.Popen(['docker','exec',PG,'sh','-c',
    'PGOPTIONS="-c default_transaction_read_only=on" pg_dump -U "$POSTGRES_USER" -d dd_round4_seed -Fc -Z1 --lock-wait-timeout=5000'],stdout=subprocess.PIPE,stderr=log)
restore=subprocess.Popen(['docker','exec','-i',AUDIT,'sh','-c',
    'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl --exit-on-error'],stdin=dump.stdout,stdout=log,stderr=log)
dump.stdout.close()
assert restore.wait()==0 and dump.wait()==0, 'Inspect private dump/restore log; never reset source'
sql('CREATE EXTENSION pg_stat_statements')
sql('ANALYZE')
integrity=json.loads(sql("SELECT json_build_object('count',count(*),'sum_ids',sum(id)::text,'full_row_xor',bit_xor(hashtextextended(f::text,0))::text) FROM dojo_finding f"))
assert integrity['count']==1000168 and integrity['sum_ids']=='500168514196' and integrity['full_row_xor']=='-4349787209074328363'
save(OUT/'raw/sql-audit-environment.json',{'image_id':image,'isolated_database':True,'streamed_copy_of':'dd_round4_seed','integrity':integrity,
    'pg_settings':json.loads(sql("SELECT json_agg(x) FROM (SELECT name,setting,unit FROM pg_settings WHERE name IN ('shared_preload_libraries','shared_buffers','work_mem','default_statistics_target','max_parallel_workers_per_gather','jit') ORDER BY name) x")),
    'statistics':'ANALYZE once on the isolated copy before either variant; no statistics changes between A and B',
    'pgss_includes_warmup':True,'http_measured_per_run':300,'http_warmup_per_run':25,
    'purpose':'Per-statement server execution totals; never pooled with the primary HTTP A/B series'})
os.environ['RC3_AUDIT_PG']='1'
for concurrency in [1,10,25]:
    for variant in (['rc2','rc3'] if concurrency!=10 else ['rc3','rc2']):
        switch(variant)
        sql('SELECT pg_stat_statements_reset()')
        target=OUT/'raw'/f'sql-audit-{variant}-c{concurrency}-http.json'
        run([sys.executable,str(ROOT/'perf-report/round5/benchmark.py'),'--url','http://127.0.0.1:48092',
            '--variant',variant,'--concurrency',str(concurrency),'--requests','300','--warmup','25','--seconds','900',
            '--timeout','90','--seed','35101','--output',str(target)],input=(PRIVATE/'accounts.json').read_bytes(),stdout=log,stderr=log)
        data=json.loads(sql("SELECT coalesce(json_agg(x),'[]') FROM (SELECT * FROM pg_stat_statements WHERE dbid=(SELECT oid FROM pg_database WHERE datname=current_database()) AND query ILIKE 'SELECT%' ORDER BY total_exec_time DESC) x"))
        save(OUT/'raw'/f'pg-stat-statements-{variant}-c{concurrency}.json',data)
        print('Server SQL audit',variant,concurrency,round(sum(row['total_exec_time'] for row in data),1),'ms',flush=True)
run([*command,'stop'],stdout=log,stderr=log)
os.environ.pop('RC3_AUDIT_PG')
switch('rc3')
save(OUT/'raw/sql-audit-complete.json',{'complete':True,'isolated_volume_retained':True,'source_settings_changed':False})
