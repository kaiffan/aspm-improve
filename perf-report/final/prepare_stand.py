#!/usr/bin/env python3
"""Create a localhost-only test Compose file. Never starts initializers or migrations."""
import argparse
import json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--private-dir',type=Path,required=True)
parser.add_argument('--runtime-env',type=Path,required=True,help='Existing 3.5.100 runtime credentials; keep outside Git')
args=parser.parse_args()
p=args.private_dir.resolve();p.mkdir(parents=True,exist_ok=True)
r=Path(__file__).resolve().parent
settings=p/'extra_settings';settings.mkdir(exist_ok=True)
(settings/'local_settings.py').write_text('import os\nMIDDLEWARE=["perf_instrument.SQLMiddleware", *MIDDLEWARE]\nCACHES["default"]["KEY_PREFIX"]=os.environ["DD_FINAL_CACHE_PREFIX"]\n')
nginx=p/'nginx.conf';nginx.write_text('worker_processes 1;\npid /var/run/defectdojo/nginx.pid;\nevents { worker_connections 1024; }\nhttp { access_log /var/log/nginx/access.log; server { listen 8080; location / { include /etc/nginx/wsgi_params; uwsgi_pass web:3031; uwsgi_read_timeout 120; } } }\n')
config={'services':{'web':{'image':'${DD_FINAL_IMAGE:-dd-final-current:3.5.100}','pull_policy':'never','entrypoint':['/wait-for-it.sh','postgres:5432','-t','30','--','/entrypoint-uwsgi.sh'],'env_file':[{'path':str(args.runtime_env.resolve()),'format':'raw'}],'environment':{'DD_FINAL_CACHE_PREFIX':'${DD_FINAL_CACHE_PREFIX:-dd-final-default}'},'volumes':['django-defectdojo_defectdojo_media:/app/media:ro',str(r/'perf_instrument.py')+':/app/perf_instrument.py:ro',str(settings)+':/app/docker/extra_settings:ro']},'nginx':{'image':'dd-api-perf-nginx:3.5.100','pull_policy':'never','entrypoint':['nginx','-c','/tmp/final-nginx.conf','-g','daemon off;'],'volumes':[str(nginx)+':/tmp/final-nginx.conf:ro'],'ports':['127.0.0.1:48084:8080']}},'networks':{'default':{'external':True,'name':'django-defectdojo_default'}},'volumes':{'django-defectdojo_defectdojo_media':{'external':True}}}
(p/'compose.json').write_text(json.dumps(config,indent=2)+'\n')
print('Prepared '+str(p/'compose.json'))
