#!/usr/bin/env python3
"""Resolve existing test accounts into a mandatory private file; never print keys."""
import argparse,json,os,subprocess
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--container',default='dd-final-web-1')
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
actors=json.loads(Path(__file__).with_name('actors.json').read_text())
source='''import json
from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from rest_framework.authtoken.models import Token
actors=ACTORS
rows=[]
for actor in actors:
    token=(Token.objects.filter(user__is_superuser=True,user__is_active=True).select_related('user').order_by('pk').first() if actor['superuser'] else Token.objects.select_related('user').get(user__username=actor['username']))
    if token is None:raise RuntimeError('Required existing benchmark account is missing')
    session=SessionStore()
    session['_auth_user_id']=str(token.user_id)
    session['_auth_user_backend']=settings.AUTHENTICATION_BACKENDS[0]
    session['_auth_user_hash']=token.user.get_session_auth_hash()
    session.save()
    rows.append({**{k:actor[k] for k in ('product','finding','test','engagement')},'token':token.key,'session':session.session_key})
print('CREDENTIALS '+json.dumps(rows))
'''.replace('ACTORS',repr(actors))
output=subprocess.check_output(['docker','exec',a.container,'python','manage.py','shell','-c',source],stderr=subprocess.DEVNULL,text=True)
rows=json.loads(next(line[12:] for line in output.splitlines() if line.startswith('CREDENTIALS ')))
a.output.parent.mkdir(parents=True,exist_ok=True)
fd=os.open(a.output,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
with os.fdopen(fd,'w') as stream:json.dump(rows,stream)
print(f'Saved {len(rows)} existing test identities to a mode-0600 private file')
