"""Run inside the isolated OrbStack lab against the stable ClusterIP."""
import base64
import hashlib
import http.client
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from http.cookies import SimpleCookie
from urllib.parse import urlencode

endpoint, mode, duration, concurrency = sys.argv[1:]
origin, username, password = creds
host = origin.split('//', 1)[1].split('/', 1)[0]
cookies = SimpleCookie()
asset = '/static/dojo/css/aspm.css'

def request(path, method='GET', payload=None, cookie=None, extra=None, target=None):
    connection = http.client.HTTPConnection(target or endpoint, timeout=4)
    headers = {'Host': host, 'Connection': 'close'}
    if cookie:
        headers['Cookie'] = cookie
    if extra:
        headers.update(extra)
    start = time.monotonic()
    try:
        connection.request(method, path, payload, headers)
        response = connection.getresponse()
        data = response.read()
        return response.status, data, response.getheaders(), round((time.monotonic()-start)*1000, 2)
    finally:
        connection.close()

def update_cookies(headers):
    for key, val in headers:
        if key.lower() == 'set-cookie':
            cookies.load(val)

def cookie_header():
    return '; '.join(k+'='+v.value for k,v in cookies.items())

status, data, headers, _ = request('/login')
assert status == 200, status
update_cookies(headers)
match = re.search(rb'name="csrfmiddlewaretoken" value="([^"]+)"', data)
assert match, 'CSRF token missing'
body = urlencode(dict(username=username,password=password,csrfmiddlewaretoken=match.group(1).decode()))
status, _, headers, _ = request('/login','POST',body,cookie_header(),{'Content-Type':'application/x-www-form-urlencoded','Referer':'http://'+host+'/login','Origin':'http://'+host})
assert status in (302,303), f'login HTTP {status}'
update_cookies(headers)
assert 'sessionid' in cookies, 'authenticated cookie missing'
cookie = cookie_header()
paths = ['/workspace/projects','/workspace/reports','/api/v2/products/?limit=1',asset]
assert request(paths[0],cookie=cookie)[0] == 200, 'projects require an authenticated session'
print(json.dumps({'event':'ready','time':time.time(),'mode':mode}),flush=True)
start = time.monotonic()
def loop(worker):
    count = 0
    while time.monotonic()-start < float(duration):
        path = paths[(worker+count)%len(paths)]
        timestamp = time.time()
        try:
            status, data, headers, latency = request(path,cookie=cookie)
            row={'time':timestamp,'path':path,'status':status,'ms':latency}
            if path == asset and count // len(paths) % 4 == 0:
                row.update(static_sha256=hashlib.sha256(data).hexdigest(),cache_control=dict(headers).get('Cache-Control',''))
        except (OSError,http.client.HTTPException) as error:
            row={'time':timestamp,'path':path,'status':0,'error':type(error).__name__}
        print(json.dumps(row),flush=True)
        count += 1
        if mode != 'bench':
            time.sleep(.18)
with ThreadPoolExecutor(max_workers=int(concurrency)) as pool:
    list(pool.map(loop,range(int(concurrency))))
