"""Submit synthetic scans under concurrent read traffic from inside the lab."""
import json
import re
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import requests

target = "http://aspm-aspm"


def reader(login, started, deadline, index, rate):
    username, password = login
    headers = {"Host": "127.0.0.1", "Connection": "close"}
    paths = ("/workspace/projects", "/workspace/reports", "/api/v2/products/?limit=1", "/static/dojo/css/aspm.css")
    with requests.Session() as client:
        client.headers.update(headers)
        page = client.get(f"{target}/login", timeout=7)
        csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page.text)[1]
        response = client.post(
            f"{target}/login", data={"username": username, "password": password, "csrfmiddlewaretoken": csrf},
            timeout=7, allow_redirects=False,
        )
        assert response.status_code == 302 and "sessionid" in client.cookies
        counts = {}
        slot = started
        step = 6 / rate if rate else 0
        while time.monotonic() < deadline:
            path = paths[index % len(paths)]
            response = client.get(target + path, timeout=7, allow_redirects=False)
            counts[response.status_code] = counts.get(response.status_code, 0) + 1
            index += 1
            slot += step
            if step:
                time.sleep(max(0, min(slot - time.monotonic(), deadline - time.monotonic())))
        return counts


def submit(fixture, burst, index):
    delivery = uuid.uuid4().hex
    fields = {
        "project_id": fixture["product_id"],
        "repository_id": fixture["repository_id"],
        "commit_sha": delivery + "00000000",
        "scanner_type": "Generic Findings Import",
        "idempotency_key": delivery,
        "pipeline_id": "stabilization-qualification",
    }
    upload = {"findings": [{"title": "Synthetic acceptance finding", "description": "Lab only", "severity": "Info"}]}
    started = time.perf_counter()
    response = requests.post(
        f"{target}/api/aspm/v1/scans/",
        headers={"Host": "127.0.0.1", "Authorization": "ASPM " + fixture["token"], "Connection": "close"},
        data=fields,
        files={"file": ("scan.json", json.dumps(upload), "application/json")},
        timeout=15,
    )
    elapsed = (time.perf_counter() - started) * 1000
    assert response.status_code == 202, response.status_code
    timing = {n: float(v) for n, v in re.findall(r"([a-z_]+);dur=([\d.]+)", response.headers.get("Server-Timing", ""))}
    assert "django" in timing, "Diagnostic web image did not emit Server-Timing"
    return {
        "batch": burst, "request": index, "client_ms": elapsed,
        "outside_django_ms": elapsed - timing["django"],
        "api_acceptance_ms": response.json()["acceptance_seconds"] * 1000, **timing,
    }


def measure(configuration, rate):
    began = time.monotonic()
    attempts = []
    with ThreadPoolExecutor(max_workers=9) as pool:
        readers = [pool.submit(reader, configuration["login"], began, began + 16, index, rate) for index in range(6)]
        time.sleep(2)
        for burst in range(8):
            jobs = [pool.submit(submit, configuration["fixture"], burst, index) for index in range(3)]
            attempts.extend(job.result() for job in jobs)
            time.sleep(0.3)
        reads = [job.result() for job in readers]
    assert all(set(results) == {200} for results in reads), reads
    return {"offered_rps": rate or None, "read_success": sum(x[200] for x in reads), "uploads": attempts}


if __name__ == "__main__":
    print(json.dumps(measure(json.loads(sys.stdin.readline()), int(sys.argv[1])), indent=2))
