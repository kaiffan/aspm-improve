#!/usr/bin/env python3
import argparse,json,subprocess
from pathlib import Path
from types import SimpleNamespace
from run_suite import switch

p=argparse.ArgumentParser();p.add_argument('--compose',type=Path,required=True);p.add_argument('--credentials',type=Path,required=True);args=p.parse_args()
root=Path(__file__).resolve().parent
accounts=json.loads(args.credentials.read_text())
with (root/'raw/extra-plans-controller.log').open('w') as log:
    for variant in ('original','current','final'):
        switch(variant,SimpleNamespace(compose=args.compose,phase='extra-plans'),accounts,log)
        subprocess.run(['docker','cp',str(root/'explain_extra.py'),'dd-final-web-1:/tmp/r4-explain-extra.py'],check=True,stdout=log,stderr=log)
        output=subprocess.check_output(['docker','exec','-i','dd-final-web-1','python','manage.py','shell','-c',"exec(open('/tmp/r4-explain-extra.py').read())"],input=json.dumps(accounts).encode(),stderr=log).decode()
        rows=[json.loads(line[5:]) for line in output.splitlines() if line.startswith('PLAN ')]
        (root/f'explain_extra_{variant}.json').write_text(json.dumps(rows,indent=2)+'\n')
        print('EXPLAIN '+variant+' '+str(len(rows))+' queries',flush=True)
