"""Paired bounded c25 SQL-shape diagnostics; run between primary load phases."""
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from run_suite import switch

R=Path(__file__).resolve().parent
private=Path('/private/tmp/dd-35100-round5')
credentials=Path('/private/tmp/dd-35100-round4/accounts.json').read_bytes();accounts=json.loads(credentials)
os.environ['DD_R5_SQL_LOG']='1'
with (R/'raw/diagnostic-pair-controller.log').open('w') as log:
    for v in ['round4','round5']:
        switch(v,SimpleNamespace(compose=private/'compose.json',phase='sql-diagnostic'),accounts,log)
        label='diagnostic-pair-'+v
        monitor=subprocess.Popen([sys.executable,str(R/'monitor.py'),str(R/'raw'/f'{label}-metrics.jsonl'),str(private/'stop-sql-pair'),'240','dd-r5-web-1'],stdout=log,stderr=log)
        subprocess.run(['docker','exec','dd-r5-web-1','python','-c',"from pathlib import Path; Path('/tmp/dd-r4-rss-stop').unlink(missing_ok=True)"],check=True,stdout=log,stderr=log)
        rss_log=(R/'raw'/f'{label}-rss.jsonl').open('wb')
        rss=subprocess.Popen(['docker','exec','-i','-e','DD_RSS_DURATION=240','dd-r5-web-1','python','-'],stdin=subprocess.PIPE,stdout=rss_log,stderr=log)
        rss.stdin.write((R/'worker_rss.py').read_bytes());rss.stdin.close()
        try:
            subprocess.run([sys.executable,str(R/'benchmark.py'),'--url','http://127.0.0.1:48085','--variant',v,'--concurrency','25','--requests','300','--warmup','25','--seconds','180','--timeout','90','--seed','35101','--stop-file',str(private/'stop-sql-pair'),'--output',str(R/'raw'/f'{label}.json')],input=credentials,check=True)
        finally:
            monitor.terminate();monitor.wait()
            subprocess.run(['docker','exec','dd-r5-web-1','touch','/tmp/dd-r4-rss-stop'],check=True,stdout=log,stderr=log)
            rss.wait(timeout=6);rss_log.close()
        target=R/'raw'/f'{label}-sql.jsonl'
        subprocess.run(['docker','cp','dd-r5-web-1:/tmp/r5-sql.jsonl',str(target)],stdout=log,stderr=log,check=True)
        subprocess.run([sys.executable,str(R/'rank_sql.py'),str(target),str(R/('sql_ranking_r4_recheck.json' if v=='round4' else 'sql_ranking_round5.json'))],check=True)
