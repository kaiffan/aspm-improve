"""Real HTTP/Celery qualification for an isolated zero-finalize stand."""
# ruff: noqa: INP001, T201, S101, PT018
import argparse
import hashlib
import json
import math
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

import requests

if sys.flags.optimize:
    msg = "Assertions must be enabled."
    raise RuntimeError(msg)
args = argparse.ArgumentParser(description=__doc__)
args.add_argument("--fixtures", type=Path, required=True)
args.add_argument("--output", type=Path, required=True)
args.add_argument("--url", default="http://127.0.0.1:8080")
args.add_argument("--rows", type=int, default=1500)
a = args.parse_args()
if urlsplit(a.url).hostname not in {"127.0.0.1", "localhost", "nginx"} or not 1 <= a.rows <= 10000:
    args.error("Use a loopback lab and a bounded 1–10000 row payload.")
creds = json.loads(Path(os.environ.get("ZF_LOAD_CREDENTIALS", "/tmp/zfq-load-private.json")).read_text(encoding="utf-8"))
base = a.url.rstrip("/")
api_headers = {"Authorization":"ASPM "+creds["token"]}
prefix = creds["nonce"]
types = {
    "Semgrep JSON Report":"semgrep/one_finding.json",
    "Trivy Scan":"trivy/scheme_2_many_vulns.json",
    "Gitleaks Scan":"gitleaks/data_one.json",
}
fixtures = {kind:(a.fixtures / name).read_bytes() for kind,name in types.items()}
generic = "Generic Findings Import"
events = []
scan_ids = set()


def api(method, path, **kwargs):
    return requests.request(method, base+"/api/aspm/v1"+path, headers=api_headers, timeout=60, **kwargs)


def page(commit, tab, **query):
    r = requests.get(base+f"/commits/{commit}/evidence", params={"tab":tab,**query},
                     cookies={"sessionid":creds["session"]},timeout=30)
    assert r.status_code == 200, r.status_code
    assert 'type="file"' not in r.text
    return r.text


def payload(key, n=1):
    return json.dumps({"findings":[{"title":f"Qualification {key} {i}","severity":"High","description":"Synthetic"}
                                  for i in range(n)]}).encode()


def upload(key, kind, sha, *, repo=0, body=None, attempt=1, pipeline="standard", expected=202):
    data = {"project_id":creds["product"],"repository_id":creds["repositories"][repo],
            "commit_sha":hashlib.sha1((prefix+sha).encode(),usedforsecurity=False).hexdigest(),
            "scanner_type":kind,"idempotency_key":prefix+"/"+key,"pipeline_id":pipeline,"job_id":kind,
            "attempt_number":attempt,"scan_scope":"repository-v1"}
    content = body if body is not None else fixtures[kind]
    start = time.perf_counter()
    result = api("POST","/scans/", data=data, files={"file":("report.json",content,"application/json")})
    latency = time.perf_counter()-start
    assert result.status_code == expected, (result.status_code,result.text[:300])
    entry = result.json()
    if expected in {200,202}:
        assert entry["artifact_sha256"] == hashlib.sha256(content).hexdigest()
        scan_ids.add(entry["id"])
    events.append({"kind":"upload","key":key,"status":expected,"seconds":latency,"bytes":len(content),"scan":entry.get("id")})
    return entry


def wait_scan(scan, expected="COMPLETED"):
    deadline = time.monotonic()+240
    while time.monotonic() < deadline:
        result = api("GET",f'/scans/{scan["id"]}/')
        assert result.status_code == 200, result.status_code
        data = result.json()
        if data["status"] in {"COMPLETED","FAILED"}:
            assert data["status"] == expected, data
            events.append({"kind":"terminal","scan":data["id"],"status":expected,"count":data["finding_count"],
                           "created_at":data["created_at"], "started_at":data["started_at"],"finished_at":data["finished_at"]})
            return data
        time.sleep(.4)
    msg = "Scan did not reach expected terminal state."
    raise TimeoutError(msg)


def report(commit):
    r = api("POST",f"/commits/{commit}/reports/",json={})
    assert r.status_code == 202, r.text[:300]
    return r.json()


def report_data(commit, report_id):
    deadline = time.monotonic()+240
    while time.monotonic()<deadline:
        listing = api("GET",f"/commits/{commit}/reports/")
        assert listing.status_code == 200
        row = next(row for row in listing.json() if row["id"]==report_id)
        assert row["status"] != "FAILED", row
        if row["status"]=="COMPLETED":
            return row
        time.sleep(.4)
    msg = "Report did not complete."
    raise TimeoutError(msg)


def downloaded(report_id):
    result = {}
    for kind in ("html","json"):
        r = api("GET",f"/reports/{report_id}/download/",params={"format":kind})
        assert r.status_code==200, r.status_code
        result[kind] = {"sha256":hashlib.sha256(r.content).hexdigest(),"bytes":len(r.content)}
    return result


def parallel(function, values, workers):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(function,values))


def main():
    profile = {}
    start = time.perf_counter()
    sequence = []
    for i,kind in enumerate(types):
        scan = upload(f"seq-{i}",kind,"sequential")
        assert scan["id"] in page(scan["commit"],"originals")
        wait_scan(scan)
        assert scan["id"] in page(scan["commit"],"findings")
        sequence.append(scan["id"])
    profile["sequential"]={"seconds":time.perf_counter()-start,"scans":sequence}
    start = time.perf_counter()
    scans = parallel(lambda pair:upload(f"triple-{pair[0]}", pair[1],"triple"),enumerate(types),3)
    done = parallel(wait_scan,scans,3)
    commit = scans[0]["commit"]
    assert len({x["commit"] for x in scans})==1
    assert len({x["id"] for x in scans})==3
    assert all(x["id"] in page(commit,"overview") for x in scans)
    replay = upload("triple-0",next(iter(types)),"triple",expected=200)
    assert replay["id"]==scans[0]["id"]
    upload("triple-0",next(iter(types)),"triple",body=b"{}",expected=409)
    profile["parallel_scanners"]={"seconds":time.perf_counter()-start,"counts":[x["finding_count"] for x in done]}
    start = time.perf_counter()
    jobs = parallel(lambda i:upload(f"job-{i}",generic,f"job-{i}",repo=i%10,body=payload(f"job-{i}")),range(100),10)
    # Bounded batch polling uses the actual status endpoint and records terminal timestamps.
    terminal = parallel(wait_scan,jobs,10)
    assert len({x["id"] for x in terminal})==100 and all(x["finding_count"]==1 for x in terminal)
    profile["independent_jobs"]={"seconds":time.perf_counter()-start,"jobs":100,"repos":10,"upload_clients":10}
    start = time.perf_counter()
    def overlap(item):
        return report(commit) if item == "export" else upload("late",next(iter(types)),"triple",attempt=2)
    pinned,late = parallel(overlap,["export","upload"],2)
    pinned_row = report_data(commit,pinned["id"])
    before = downloaded(pinned["id"])
    wait_scan(late)
    after = downloaded(pinned["id"])
    members = pinned_row["manifest"]["scans"]
    assert before==after and len(members)==3
    assert before["json"]["sha256"]==pinned_row["checksums"]["json"]
    downloaded_json = api("GET",f'/reports/{pinned["id"]}/download/',params={"format":"json"}).json()
    assert len(members) == len({item["id"] for item in members})
    assert all(item["id"] in json.dumps(downloaded_json) for item in members)
    profile["overlap"]={"seconds":time.perf_counter()-start,"members":members,"files":after}
    start = time.perf_counter()
    good = upload("mixed-good",next(iter(types)),"large")
    wait_scan(good)
    failed = upload("mixed-failed","Trivy Scan","large",body=b"invalid report")
    wait_scan(failed, "FAILED")
    large = upload("large",generic,"large",body=payload("large",a.rows))
    assert large["commit"] == good["commit"] == failed["commit"]
    saw_processing = False
    deadline = time.monotonic()+20
    while time.monotonic() < deadline:
        overview = page(large["commit"],"overview")
        if "<dt>PROCESSING</dt>" in overview:
            assert "<dt>FAILED</dt>" in overview and "<dt>COMPLETED</dt>" in overview
            assert "INCOMPLETE" in overview and large["id"] not in overview
            saw_processing = True
            break
        if "<dt>ACCEPTED</dt>" not in overview:
            break
        time.sleep(.1)
    assert saw_processing, "Worker completed before the mixed-state sample."
    profile["mixed_states"]={"observed":["COMPLETED","PROCESSING","FAILED"],"coverage":"INCOMPLETE"}
    finished = wait_scan(large)
    assert finished["finding_count"]==a.rows
    assert large["id"] in page(large["commit"],"overview")
    assert large["id"] in page(large["commit"],"findings")
    profile["large_commit"]={"seconds":time.perf_counter()-start,"observations":finished["finding_count"],"scan_id":large["id"]}
    all_uploads = sorted(e["seconds"] for e in events if e["kind"]=="upload" and e["status"]==202)
    profile["acceptance"]={"p50_ms":1000*statistics.median(all_uploads),"p95_ms":1000*all_uploads[math.ceil(.95*len(all_uploads))-1]}
    return profile


try:
    result = main()
finally:
    a.output.write_text(json.dumps({"scenarios":locals().get("result"),"events":events,"distinct_scan_ids":len(scan_ids)},indent=2)+"\n",encoding="utf-8")
