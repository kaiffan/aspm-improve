"""Exercise an explicitly owned local ASPM installation with synthetic scan reports."""

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

import requests


def percentile(samples, quantile):
    ordered = sorted(samples)
    return round(ordered[math.ceil(len(ordered) * quantile) - 1], 4)


class Runner:
    def __init__(self, base, credentials):
        self.base = base.rstrip("/")
        self.product = credentials["product_id"]
        self.fixtures = credentials["fixtures"]
        self.run_id = uuid.uuid4().hex[:12]

    def api(self, method, path, expected=200, *, slot, **kwargs):
        headers = {"Authorization": "ASPM " + self.fixtures[slot]["token"]}
        response = requests.request(method, self.base + "/api/aspm/v1/" + path, headers=headers, timeout=45, **kwargs)
        if response.status_code != expected:
            raise RuntimeError(f"Unexpected ASPM API status {response.status_code}; expected {expected}")
        return response

    def submit(self, index):
        slot = index % len(self.fixtures)
        report = json.dumps({"findings": [{"title": f"Qualification fixture {self.run_id}-{index}", "severity": "High", "description": "Synthetic ingestion evidence"}]}).encode()
        data = {
            "project_id": self.product,
            "repository_id": self.fixtures[slot]["repository_id"],
            "commit_sha": hashlib.sha256(f"{self.run_id}/{index}".encode()).hexdigest()[:40],
            "scanner_type": "Generic Findings Import",
            "idempotency_key": f"qualification/{self.run_id}/{index}",
            "pipeline_id": f"qualification-{self.run_id}",
            "job_id": f"scan-{index}",
        }
        began = time.monotonic()
        result = self.api("POST", "scans/", expected=202, slot=slot, data=data, files={"file": ("fixture.json", report, "application/json")}).json()
        if result["artifact_sha256"] != hashlib.sha256(report).hexdigest():
            raise RuntimeError("Original checksum mismatch on receipt")
        return {"slot": slot, "id": result["id"], "commit": result["commit"], "sha256": result["artifact_sha256"], "accept_seconds": time.monotonic() - began}

    def wait_scan(self, scan):
        deadline = time.monotonic() + 150
        while time.monotonic() < deadline:
            row = self.api("GET", f"scans/{scan['id']}/", slot=scan["slot"]).json()
            if row["status"] == "FAILED":
                raise RuntimeError("Synthetic scan failed")
            if row["status"] == "COMPLETED":
                if row["finding_count"] != 1:
                    raise RuntimeError("Unexpected observation count")
                return
            time.sleep(.25)
        raise TimeoutError("Timed out waiting for scan completion")

    def verify_downloads(self, scan):
        slot = scan["slot"]
        body = self.api("GET", f"scans/{scan['id']}/artifact/", slot=slot).content
        if hashlib.sha256(body).hexdigest() != scan["sha256"]:
            raise RuntimeError("Original artifact checksum mismatch on download")
        report = self.api("POST", f"commits/{scan['commit']}/reports/", expected=202, slot=slot, json={}).json()["id"]
        deadline = time.monotonic() + 150
        while time.monotonic() < deadline:
            rows = self.api("GET", f"commits/{scan['commit']}/reports/", slot=slot).json()
            row = next(item for item in rows if item["id"] == report)
            if row["status"] == "FAILED":
                raise RuntimeError("Generated report failed")
            if row["status"] == "COMPLETED":
                for kind in ("json", "html"):
                    content = self.api("GET", f"reports/{report}/download/", slot=slot, params={"format": kind}).content
                    if hashlib.sha256(content).hexdigest() != row["checksums"][kind]:
                        raise RuntimeError("Generated report checksum mismatch on download")
                return {"original": True, "generated_json": True, "generated_html": True}
            time.sleep(.25)
        raise TimeoutError("Timed out waiting for report export")

    def load(self):
        started = time.monotonic()
        with ThreadPoolExecutor(max_workers=10) as pool:
            scans = list(pool.map(self.submit, range(100)))
            accept_seconds = time.monotonic() - started
            list(pool.map(self.wait_scan, scans))
        end_to_end = time.monotonic() - started
        if len({scan["id"] for scan in scans}) != len(scans):
            raise RuntimeError("Scan job identifiers were not unique")
        timings = [scan["accept_seconds"] for scan in scans]
        return {
            "scope": "synthetic local ARM64 smoke",
            "jobs": len(scans),
            "scanner": "Generic Findings Import",
            "repositories": len(self.fixtures),
            "repository_scoped_tokens": len(self.fixtures),
            "submission_clients": 10,
            "submission_wall_seconds": round(accept_seconds, 4),
            "accept_latency_seconds": {
                "p50": round(statistics.median(timings), 4),
                "p95": percentile(timings, .95),
                "p99": percentile(timings, .99),
            },
            "completed_throughput_per_second": round(len(scans) / end_to_end, 3),
            "end_to_end_seconds": round(end_to_end, 4),
            "download_checksum_verification": self.verify_downloads(scans[0]),
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--mode", choices=("load", "submit", "recover"), default="load")
    args = parser.parse_args()
    parsed = urlsplit(args.url)
    if parsed.hostname not in {"localhost", "127.0.0.1"} or parsed.scheme != "http" or parsed.username or parsed.path not in {"", "/"}:
        parser.error("The target must be an explicitly owned loopback HTTP lab")
    credentials = json.load(sys.stdin)
    runner = Runner(args.url, credentials)
    if args.mode == "load":
        if len(runner.fixtures) != 10:
            parser.error("The 100-job load uses exactly ten repository-scoped tokens")
        result = runner.load()
    elif args.mode == "submit":
        result = runner.submit(0)
    else:
        runner.wait_scan(credentials["scan"])
        result = {"completed_after_broker_restart": True, "checksums": runner.verify_downloads(credentials["scan"])}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
