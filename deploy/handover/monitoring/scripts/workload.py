"""Exercise an isolated ASPM API with synthetic scan and report data."""
# ruff: noqa: INP001
import argparse
import json
import statistics
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import requests


def quantile(samples, value):
    return round(statistics.quantiles(samples, n=100, method="inclusive")[int(value * 100) - 1], 4)


class Workload:
    def __init__(self, base, fixture):
        self.base = base
        self.fixture = fixture

    def call(self, method, path, *expected, **kwargs):
        response = requests.request(method, self.base + path, headers={"Authorization": "ASPM " + self.fixture["token"]}, timeout=20, **kwargs)
        if response.status_code not in expected:
            msg = f"{method} received HTTP {response.status_code}, expected {expected}"
            raise RuntimeError(msg)
        return response

    def upload(self, delivery, body, expected):
        return self.call(
            "POST", "/api/aspm/v1/scans/", expected,
            data={"project_id": self.fixture["product_id"], "repository_id": self.fixture["repository_id"],
                  "commit_sha": delivery + "00000000", "idempotency_key": delivery,
                  "scanner_type": "Semgrep JSON Report", "pipeline_id": "synthetic-monitoring"},
            files={"file": ("scan.json", body, "application/json")},
        ).json()

    def submit_and_wait(self, body):
        start = time.monotonic()
        scan = self.upload(uuid.uuid4().hex, body, 202)
        accepted = time.monotonic() - start
        return self.wait_scan(scan), accepted, time.monotonic() - start

    def wait_scan(self, scan):
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            doc = self.call("GET", f"/api/aspm/v1/scans/{scan['id']}/", 200).json()
            if doc["status"] in {"COMPLETED", "FAILED"}:
                return doc
            time.sleep(0.5)
        msg = "Synthetic scan never reached a terminal state"
        raise TimeoutError(msg)

    def verify_flows(self, body):
        delivery = uuid.uuid4().hex
        valid = self.upload(delivery, body, 202)
        duplicate = self.upload(delivery, body, 200)
        assert valid["id"] == duplicate["id"]
        assert self.wait_scan(valid)["status"] == "COMPLETED"
        failed = self.upload(uuid.uuid4().hex, b"invalid report body", 202)
        assert self.wait_scan(failed)["status"] == "FAILED"
        path = f"/api/aspm/v1/commits/{valid['commit']}/reports/"
        report = self.call("POST", path, 202, json={}).json()
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            current = next(row for row in self.call("GET", path, 200).json() if row["id"] == report["id"])
            if current["status"] == "COMPLETED":
                for kind in ("html", "json"):
                    self.call("GET", f"/api/aspm/v1/reports/{report['id']}/download/?format={kind}", 200)
                return {"scan_http": 202, "duplicate_http": 200, "good_scan": "COMPLETED", "bad_scan": "FAILED", "report": "COMPLETED"}
            if current["status"] == "FAILED":
                msg = "Synthetic report generation failed"
                raise RuntimeError(msg)
            time.sleep(0.5)
        msg = "Synthetic report never completed"
        raise TimeoutError(msg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("scan_file")
    parser.add_argument("--count", type=int, default=16)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--flows", action="store_true")
    args = parser.parse_args()
    workload = Workload(args.url.rstrip("/"), json.load(sys.stdin))
    with open(args.scan_file, "rb") as source:
        scan = source.read()
    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(workload.submit_and_wait, [scan] * args.count))
    elapsed = time.monotonic() - start
    assert all(doc["status"] == "COMPLETED" for doc, _, _ in results)
    report = {"scans_completed": len(results), "completion_per_second": round(len(results) / elapsed, 3),
              "acceptance_p95_seconds": quantile([seconds for _, seconds, _ in results], .95),
              "completion_p95_seconds": quantile([seconds for _, _, seconds in results], .95)}
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        def read(_):
            before = time.monotonic()
            workload.call("GET", "/api/aspm/v1/scans/unresolved/", 404)
            return time.monotonic() - before

        start = time.monotonic()
        durations = list(pool.map(read, range(100)))
        report.update(http_probe_rps=round(100 / (time.monotonic() - start), 2), http_probe_p95_seconds=quantile(durations, .95))
    if args.flows:
        report["flows"] = workload.verify_flows(scan)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
