"""Repeated read-only HTML renders on the final isolated validation copy."""
import hashlib
import http.client
import json
import re
import subprocess
from lab import OUT,PRIVATE,WEB,save
assert json.loads((OUT/'raw/validation-complete.json').read_text())['complete']
code="from django.db import connection;assert connection.settings_dict['NAME']=='aspm_rc3_validation';print('COPY_OK')"
result=subprocess.check_output(['docker','exec',WEB,'python','manage.py','shell','-c',code],text=True)
assert 'COPY_OK' in result
dynamic=[]
for actor in [0,1]:
    account=json.loads((PRIVATE/'accounts-copy.json').read_text())[actor]
    for path in ['/dashboard','/asset']:
        observations=[]
        for _ in range(3):
            conn=http.client.HTTPConnection('127.0.0.1',48092,timeout=90)
            conn.request('GET',path,headers={'Cookie':'sessionid='+account['session']})
            response=conn.getresponse();body=response.read();assert response.status==200;conn.close()
            warning=re.search(rb'var warningTime = "([^"]*)";',body);assert warning
            normalized=body
            for token in re.findall(rb'(?:name="csrfmiddlewaretoken" value="|X-CSRFToken": ")([^"]+)"',body):normalized=normalized.replace(token,b'<csrf>')
            normalized=re.sub(rb'var warningTime = "[^"]*";',b'var warningTime = "<dynamic>";',normalized)
            observations.append({'bytes':len(body),'warning_time_length':len(warning[1]),'bytes_without_warning_time':len(body)-len(warning[1]),'normalized_hash':hashlib.sha256(normalized).hexdigest()})
        assert len({row['normalized_hash'] for row in observations})==1, 'Investigate other dynamic HTML differences'
        dynamic.append({'actor':actor,'path':path,'observations':observations,'only_csrf_and_warning_time_change':True})
save(OUT/'raw/html-dynamic-size-check.json',dynamic)
print('Verified repeated HTML: only CSRF and session warning timestamp change')
