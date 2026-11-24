"""Real HTTP + real Celery smoke on this task's private local runtime."""
# ruff: noqa: INP001, T201, S101, PT018
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import requests

if sys.flags.optimize:
    msg = "Qualification requires Python assertions enabled."
    raise RuntimeError(msg)

credentials = json.loads(Path(os.environ.get("ZERO_HTTP_CREDENTIALS", "/zero-runtime/credentials.json")).read_text(encoding="utf-8"))
base = "http://http:8080"
api = requests.Session()
api.headers["Authorization"] = "ASPM " + credentials["token"]
browser = requests.Session()
browser.cookies["sessionid"] = credentials["session"]
checks = {}


def upload(key, scanner, payload, attempt=3, **changes):
    data = {"project_id": credentials["product_id"], "repository_id": credentials["repository_id"],
            "commit_sha": os.environ.get("ZERO_HTTP_SHA", "a" * 40), "scanner_type": scanner, "idempotency_key": key,
            "pipeline_id": credentials["run"], "job_id": scanner, "attempt_number": attempt,
            "scan_scope": "repository-v1", **changes}
    return api.post(base + "/api/aspm/v1/scans/", data=data,
                    files={"file": ("report.json", payload, "application/json")}, timeout=30)


def wait_scan(identifier):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        result = api.get(base + "/api/aspm/v1/scans/" + identifier + "/", timeout=20)
        assert result.status_code == 200, result.status_code
        row = result.json()
        if row["status"] in {"COMPLETED", "FAILED"}:
            assert row["status"] == "COMPLETED", row
            return row
        time.sleep(1)
    msg = "scan processing"
    raise TimeoutError(msg)


def main():
    for _ in range(60):
        try:
            if requests.get(base + "/login", timeout=5).status_code < 500:
                break
        except requests.ConnectionError:
            pass
        time.sleep(1)
    else:
        msg = "HTTP readiness"
        raise TimeoutError(msg)
    fixtures = Path("/app/unittests/scans")
    # Production image includes these fixtures; they are not sent to the user or external services.
    paths = [("Semgrep JSON Report", "semgrep/one_finding.json"),
             ("Trivy Scan", "trivy/scheme_2_many_vulns.json"),
             ("Gitleaks Scan", "gitleaks/data_one.json")]
    ids = []
    for i, (scanner, relative) in enumerate(paths):
        payload = (fixtures / relative).read_bytes()
        response = upload("http-image-" + credentials["run"] + "/" + str(i), scanner, payload)
        assert response.status_code == 202, response.text[:500]
        row = response.json()
        if credentials["commit_id"] is None:
            credentials["commit_id"] = row["commit"]
        assert row["commit"] == credentials["commit_id"]
        page = browser.get(base + f'/commits/{row["commit"]}/evidence?tab=originals', timeout=20)
        assert page.status_code == 200 and row["id"] in page.text, page.status_code
        wait_scan(row["id"])
        observations = browser.get(base + f'/commits/{row["commit"]}/evidence?tab=findings', timeout=20)
        assert observations.status_code == 200 and row["id"] in observations.text
        ids.append(row["id"])
    checks["sequential_semgrep_trivy_gitleaks_one_upload_each"] = True
    overview = browser.get(base + f'/commits/{credentials["commit_id"]}', timeout=20)
    # The canonical commit route may have a trailing slash configured by the router.
    if overview.status_code == 404:
        overview = browser.get(base + f'/commits/{credentials["commit_id"]}/', timeout=20)
    checks["evidence_live_without_finalize"] = True
    replay = upload("http-image-" + credentials["run"] + "/0", paths[0][0], (fixtures / paths[0][1]).read_bytes())
    assert replay.status_code == 200 and replay.json()["id"] == ids[0]
    checks["http_idempotent_replay"] = True
    reports_url = base + f'/api/aspm/v1/commits/{credentials["commit_id"]}/reports/'
    response = api.post(reports_url, json={}, timeout=20)
    assert response.status_code == 202, response.text[:500]
    report = response.json()
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        rows = api.get(reports_url, params={"after": report["version"] - 1}, timeout=20).json()
        current = next(row for row in rows if row["id"] == report["id"])
        if current["status"] == "COMPLETED":
            break
        assert current["status"] != "FAILED", current
        time.sleep(1)
    else:
        msg = "report generation"
        raise TimeoutError(msg)
    blobs = {}
    for kind in ("html", "json"):
        response = api.get(base + f'/api/aspm/v1/reports/{report["id"]}/download/', params={"format": kind}, timeout=30)
        assert response.status_code == 200
        blobs[kind] = response.content
        assert hashlib.sha256(response.content).hexdigest() == current["checksums"][kind]
        assert response.headers["Cache-Control"] == "private, no-store"
    checks["real_worker_export_without_finalize_and_protected_hashes"] = True
    late = upload("http-image-" + credentials["run"] + "/late", paths[0][0], (fixtures / paths[0][1]).read_bytes(), attempt=4)
    assert late.status_code == 202
    wait_scan(late.json()["id"])
    for kind in ("html", "json"):
        response = api.get(base + f'/api/aspm/v1/reports/{report["id"]}/download/', params={"format": kind}, timeout=30)
        assert response.content == blobs[kind]
    checks["late_scan_preserves_old_report_bytes"] = True
    denied = upload("http-denied-" + credentials["run"], paths[0][0], (fixtures / paths[0][1]).read_bytes(), project_id=credentials["product_id"] + 10000)
    assert denied.status_code == 403
    anonymous = requests.get(base + f'/api/aspm/v1/reports/{report["id"]}/download/', timeout=20)
    assert anonymous.status_code in {401, 403}
    page = browser.get(base + f'/commits/{credentials["commit_id"]}/evidence?tab=originals', timeout=20)
    assert 'type="file"' not in page.text and "multipart/form-data" not in page.text
    checks["rbac_and_no_browser_upload"] = True
    assert not current["manifest"]["complete"]
    checks["unknown_coverage_never_complete"] = True
    output = {"passed": all(checks.values()), "checks": checks, "commit_id": credentials["commit_id"],
              "scan_ids": ids, "late_scan_id": late.json()["id"], "report_id": report["id"],
              "checksums": current["checksums"]}
    print(json.dumps(output))


main()
