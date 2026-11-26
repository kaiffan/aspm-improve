"""Sample a loopback HTTPS lab URL and keep retries separate from raw availability."""
import hashlib
import http.client
import json
import re
import ssl
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from http.cookies import SimpleCookie
from urllib.parse import urlencode

paths = ("/workspace/projects", "/workspace/reports", "/api/v2/products/?limit=1", "/static/dojo/css/aspm.css")


def send(path, *, method="GET", body=None, cookie="", slow=False):
    connection = http.client.HTTPSConnection("localhost", 18736, timeout=8, context=tls)
    headers = {"Connection": "close", "Cookie": cookie}
    if method == "POST":
        headers.update({"Content-Type": "application/x-www-form-urlencoded", "Origin": "https://localhost:18736"})
    begun = time.perf_counter()
    try:
        connection.request(method, path, body, headers)
        incoming = connection.getresponse()
        output = None
        if slow:
            digest = hashlib.sha256()
            size = 0
            while chunk := incoming.read(65536):
                digest.update(chunk)
                size += len(chunk)
                time.sleep(0.03)
            output = {"sha256": digest.hexdigest(), "bytes": size}
        else:
            output = incoming.read()
        return incoming.status, incoming.headers, output, round((time.perf_counter()-begun)*1000, 3)
    finally:
        connection.close()


def update(cookies, headers):
    for value in headers.get_all("Set-Cookie") or ():
        cookies.load(value)


def authorization(login):
    status, headers, html, _ = send("/login")
    assert status == 200, status
    jar = SimpleCookie()
    update(jar, headers)
    token = re.search(rb'name="csrfmiddlewaretoken" value="([^"]+)"', html)[1].decode()
    raw = urlencode({"username": login[0], "password": login[1], "csrfmiddlewaretoken": token})
    status, headers, _, _ = send("/login", method="POST", body=raw, cookie=jar.output(attrs=[], header="", sep=";"))
    update(jar, headers)
    assert status == 302 and "sessionid" in jar, status
    return jar.output(attrs=[], header="", sep=";")


def watch(index, mode, cookie, deadline):
    for i in range(99999):
        if time.monotonic() >= deadline:
            break
        path = paths[(index+i) % len(paths)]
        first = time.time()
        record = {"at": first, "mode": mode, "path": path}
        statuses = []
        for attempt in range(3 if mode == "retry" else 1):
            try:
                status, _, output, _ = send(path, cookie=cookie)
                statuses.append(status)
                if status == 200:
                    if path.startswith("/static/"):
                        record["sha256"] = hashlib.sha256(output).hexdigest()
                    break
            except (OSError, http.client.HTTPException) as error:
                statuses.append(type(error).__name__)
            if attempt < 2 and mode == "retry":
                time.sleep(.15)
        record.update(attempts=statuses, ms=round((time.time()-first)*1000,2))
        print(json.dumps(record), flush=True)
        time.sleep(.20)


def download(artifact, cookie):
    begin = time.time()
    code, _, body, ms = send(artifact, cookie=cookie, slow=True)
    print(json.dumps({"mode": "in_flight", "at": begin, "status": code, "ms": ms, **body}), flush=True)


if __name__ == "__main__":
    tls = ssl.create_default_context(cafile=sys.argv[1])
    duration = int(sys.argv[2])
    configuration = json.load(sys.stdin)
    session = authorization(configuration["login"])
    print(json.dumps({"event": "ready", "at": time.time()}), flush=True)
    deadline = time.monotonic() + duration
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(watch, index, mode, session, deadline)
                   for index, mode in enumerate(("raw", "raw", "retry", "retry"))]
        futures.append(pool.submit(download, configuration["artifact"], session))
        for future in futures:
            future.result()
