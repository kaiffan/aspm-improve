"""Measure a fixed small workload in an isolated ASPM lab through ClusterIP."""
from concurrent.futures import ThreadPoolExecutor
import collections
import json
import math
import re
import sys
import time
import uuid

import requests

site = "http://aspm-aspm"
auth = json.load(sys.stdin)
base_headers = {"Host": "127.0.0.1", "Connection": "close"}
paths = ("/workspace/projects", "/workspace/reports", "/api/v2/products/?limit=1", "/static/dojo/css/aspm.css")


def read(index, began, deadline):
    with requests.Session() as client:
        client.headers.update(base_headers)
        try:
            r = client.get(site + "/login", timeout=5)
            csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)[1]
            r = client.post(site + "/login", data={"username": auth["admin"], "password": auth["password"], "csrfmiddlewaretoken": csrf},
                            allow_redirects=False, timeout=8)
            assert r.status_code == 302 and "sessionid" in client.cookies
        except (requests.RequestException, AssertionError, TypeError) as exc:
            return [{"status": "login-" + type(exc).__name__, "ms": None}]
        schedule = began
        samples = []
        while time.monotonic() < deadline:
            started = time.monotonic()
            path = paths[index % len(paths)]
            try:
                r = client.get(site + path, allow_redirects=False, timeout=5)
                result = r.status_code
            except requests.RequestException as exc:
                result = type(exc).__name__
            samples.append({"status": result, "ms": 1000 * (time.monotonic() - started)})
            index += 1
            schedule += 6 / 75
            time.sleep(max(0, min(schedule - time.monotonic(), deadline - time.monotonic())))
        return samples


def upload(index):
    key = uuid.uuid4().hex
    fields = {"project_id": auth["product"], "repository_id": auth["repository"],
              "commit_sha": key + "00000000", "scanner_type": "Generic Findings Import",
              "idempotency_key": key, "pipeline_id": "enterprise-qualification"}
    data = {"findings": [{"title": "Synthetic acceptance finding", "description": "Qualification only", "severity": "Info"}]}
    headers = base_headers | {"Authorization": "ASPM " + auth["ingestion"]}
    start = time.monotonic()
    try:
        response = requests.post(site + "/api/aspm/v1/scans/", headers=headers, data=fields,
                                 files={"file": ("acceptance.json", json.dumps(data), "application/json")}, timeout=10)
        status = response.status_code
        record = {"status": status, "ms": 1000 * (time.monotonic() - start)}
        if status == 202:
            payload = response.json()
            record.update(id=payload["id"], api_ms=1000 * payload["acceptance_seconds"])
    except requests.RequestException as exc:
        record = {"status": type(exc).__name__, "ms": 1000 * (time.monotonic() - start)}
    return record


def quantiles(values):
    ordered = sorted(values)
    return {f"p{p}": round(ordered[math.ceil(p / 100 * len(ordered)) - 1], 2) for p in (50, 95, 99)} if ordered else {}


began = time.monotonic()
scans = []
with ThreadPoolExecutor(max_workers=9) as pool:
    readers = [pool.submit(read, i, began, began + 16) for i in range(6)]
    time.sleep(2)
    for burst in range(8):
        scans.extend(pool.map(upload, range(3)))
        time.sleep(.3)
    read_rows = [row for future in readers for row in future.result()]
upload_window = time.monotonic() - began
accepted = {row["id"] for row in scans if row["status"] == 202}
headers = base_headers | {"Authorization": "ASPM " + auth["ingestion"]}
completed = {}
deadline = time.monotonic() + 125
while set(completed) != accepted and time.monotonic() < deadline:
    for scan in sorted(accepted - set(completed)):
        response = requests.get(site + f"/api/aspm/v1/scans/{scan}/", headers=headers, timeout=5)
        if response.ok:
            detail = response.json()
            if detail["status"] in ("COMPLETED", "FAILED"):
                completed[scan] = {"status": detail["status"], "timings": detail["timings"], "finding_count": detail["finding_count"]}
    if set(completed) != accepted:
        time.sleep(3)
outcomes = list(completed.values())
n = sum(row["status"] == "COMPLETED" and row["finding_count"] == 1 for row in outcomes)
read_status = collections.Counter(map(str,(row["status"] for row in read_rows)))
submit_status = collections.Counter(map(str,(row["status"] for row in scans)))
values = {"read_statuses": dict(read_status), "read_achieved_rps": round(read_status["200"] / 16, 3),
          "read_latency_ms": quantiles(r["ms"] for r in read_rows if r["status"] == 200),
          "submit_statuses": dict(submit_status), "accept_client_ms": quantiles(r["ms"] for r in scans if r["status"] == 202),
          "accept_api_ms": quantiles(r["api_ms"] for r in scans if r["status"] == 202),
          "completed": n, "elapsed_until_observed_seconds": round(time.monotonic() - began, 3), "load_window_seconds": round(upload_window,3),
          "rows": read_rows, "scan_acceptance": [{k:v for k,v in r.items() if k!="id"} for r in scans], "scan_outcomes": outcomes}
print(json.dumps(values, indent=2))
