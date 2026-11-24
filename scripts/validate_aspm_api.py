# ruff: noqa: INP001, S101, T201
"""Real HTTP/Celery acceptance and bounded concurrent submission measurements; no credentials in output."""

import argparse
import hashlib
import json
import math
import statistics
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:48094")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    credentials = json.loads(args.credentials.read_text())
    base = args.base_url.rstrip("/")
    prefix = "/api/aspm/v1"
    namespace = uuid.uuid4().hex
    samples = []
    primary_repository = f"https://github.com/example/aspm-runtime-{namespace}"

    def request(path, *, data=None, content_type=None, human=False, expect=(200,), binary=False):
        headers = {"Cookie": f"sessionid={credentials['session']}"} if human else {"Authorization": f"ASPM {credentials['token']}"}
        if content_type:
            headers["Content-Type"] = content_type
        start = time.monotonic()
        req = urllib.request.Request(base + path, data=data, headers=headers)  # noqa: S310 -- operator-selected HTTP test endpoint
        try:
            response = urllib.request.urlopen(req, timeout=180)  # noqa: S310 -- operator-selected HTTP test endpoint
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read()
            code = response.status
        if code not in expect:
            msg = f"Unexpected HTTP {code} for {path}; expected {expect}"
            raise RuntimeError(msg)
        return (body if binary or not body else json.loads(body)), time.monotonic() - start, code

    def upload(key, scanner, report, *, repository=None, project=None):
        fields = {"project_id": project or credentials["product_id"], "repository_url": repository or primary_repository,
                  "commit_sha": "c" * 40, "scanner_type": scanner, "idempotency_key": namespace + "/" + key,
                  "pipeline_id": namespace, "job_id": key, "attempt_number": 1}
        boundary = "aspm-" + uuid.uuid4().hex
        chunks = []
        for field_name, value in fields.items():
            chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{field_name}"\r\n\r\n{value}\r\n'.encode())
        chunks.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="scan.json"\r\nContent-Type: application/json\r\n\r\n'.encode(), report, f"\r\n--{boundary}--\r\n".encode()])
        payload, seconds, code = request(prefix + "/scans/", data=b"".join(chunks), content_type=f"multipart/form-data; boundary={boundary}", expect=(200, 202, 403))
        return payload, seconds, code

    def wait_scan(identifier):
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            payload, _, _ = request(f"{prefix}/scans/{identifier}/", human=True)
            if payload["status"] in {"COMPLETED", "FAILED"}:
                if payload["status"] != "COMPLETED":
                    msg = f"Scan failed: {identifier}: {payload['error_code']}"
                    raise RuntimeError(msg)
                return payload
            time.sleep(0.5)
        msg = f"Timed out waiting for scan {identifier}"
        raise TimeoutError(msg)

    scans_root = Path(__file__).resolve().parents[1] / "unittests/scans"
    originals = [("semgrep", "Semgrep JSON Report", (scans_root / "semgrep/one_finding.json").read_bytes()),
                 ("trivy", "Trivy Scan", (scans_root / "trivy/scheme_2_many_vulns.json").read_bytes())]
    accepted = []
    for key, scanner, report in originals:
        result, seconds, code = upload(key, scanner, report)
        assert code == 202
        accepted.append(result)
        samples.append(seconds)
        downloaded, _, _ = request(f"{prefix}/scans/{result['id']}/artifact/", human=True, binary=True)
        assert downloaded == report
        assert result["artifact_sha256"] == hashlib.sha256(report).hexdigest()
    assert accepted[0]["commit"] == accepted[1]["commit"]
    repeated, _, code = upload(*originals[0])
    assert code == 200
    assert repeated["id"] == accepted[0]["id"]
    generic = json.dumps({"findings": [{"title": "Concurrent HTTP fixture", "description": "Synthetic acceptance", "severity": "High", "cwe": 79}]}).encode()
    with ThreadPoolExecutor(max_workers=8) as pool:
        duplicates = list(pool.map(lambda _: upload("parallel", "Generic Findings Import", generic), range(8)))
    assert sorted(code for _, _, code in duplicates) == [200] * 7 + [202]
    assert len({row[0]["id"] for row in duplicates}) == 1
    accepted.append(duplicates[0][0])
    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=8) as pool:
        independent = list(pool.map(lambda i: upload(f"independent-{i}", "Generic Findings Import", generic, repository=f"https://github.com/example/runtime-{namespace}-{i}"), range(24)))
    concurrent_seconds = time.monotonic() - start
    assert all(code == 202 for _, _, code in independent)
    all_scans = accepted + [row[0] for row in independent]
    samples.extend(row[1] for row in independent)
    completed = [wait_scan(scan["id"]) for scan in all_scans]
    assert len({row["id"] for row in completed}) == len(all_scans)
    for path in (f"{prefix}/scans/{accepted[0]['id']}/",):
        request(path, expect=(200,))
    _, _, denied = upload("foreign-product", "Generic Findings Import", generic, project=credentials["hidden_product_id"])
    assert denied == 403
    commit_id = accepted[0]["commit"]
    scan_set, _, _ = request(f"{prefix}/commits/{commit_id}/finalize/", data=json.dumps({"expected_scanners": ["Semgrep JSON Report", "Trivy Scan", "Generic Findings Import"]}).encode(), content_type="application/json", expect=(201,))
    report, _, _ = request(f"{prefix}/commits/{commit_id}/reports/", data=json.dumps({"scan_set_id": scan_set["id"]}).encode(), content_type="application/json", expect=(202,))
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        reports, _, _ = request(f"{prefix}/commits/{commit_id}/reports/", human=True)
        ready = next(row for row in reports if row["id"] == report["id"])
        if ready["status"] == "COMPLETED":
            break
        assert ready["status"] != "FAILED"
        time.sleep(0.5)
    else:
        msg = "Timed out waiting for generated report"
        raise TimeoutError(msg)
    artifact, _, _ = request(f"{prefix}/reports/{report['id']}/download/?format=json", human=True, binary=True)
    generated = json.loads(artifact)
    assert generated["report"]["complete"]
    assert any("CVE-2020-15999" in row["vulnerability_ids"] for row in generated["observations"])
    assert {row["id"] for row in generated["report"]["scans"]} == {row["id"] for row in accepted}
    assert len(generated["observations"]) == sum(scan["finding_count"] for scan in completed[:3])
    late, _, code = upload("late-arrival", "Generic Findings Import", generic)
    assert code == 202
    wait_scan(late["id"])
    after, _, _ = request(f"{prefix}/reports/{report['id']}/download/?format=json", human=True, binary=True)
    assert artifact == after
    output = {"scenario": "Real HTTP, PostgreSQL, Valkey and prefork Celery; synthetic scanner fixtures",
              "scan_count": len(all_scans), "independent_repositories": 24, "concurrency": 8,
              "duplicate_request_codes": sorted(code for _, _, code in duplicates),
              "upload_seconds": {"median": statistics.median(samples), "p95": sorted(samples)[math.ceil(len(samples) * 0.95) - 1], "max": max(samples)},
              "upload_samples_seconds": samples, "percentile_method": "nearest rank",
              "concurrent_24_upload_seconds": concurrent_seconds,
              "phases": [{"scanner": row["scanner"], "finding_count": row["finding_count"], **row["timings"]} for row in completed],
              "report_timings": ready["timings"], "report_checksums": ready["checksums"],
              "commit_id": commit_id, "repository_url": primary_repository, "report_id": report["id"],
              "checks": {"byte_exact_originals": True, "same_commit": True, "idempotent_concurrent_posts": True, "all_workers_completed": True,
                        "exact_report_membership": True, "immutable_report_after_late_upload": True, "cross_product_denied": True, "cve_preserved": True}}
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"scans": len(all_scans), "checks": output["checks"], "upload_seconds": output["upload_seconds"]}))


if __name__ == "__main__":
    main()
