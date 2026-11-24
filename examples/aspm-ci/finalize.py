"""Wait for CI deliveries, freeze the commit set and download platform-generated HTML/JSON."""
# ruff: noqa: INP001, T201
import argparse
import json
import os
import shutil
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deliveries", nargs="+", type=Path, help="JSON responses returned by upload.sh")
    parser.add_argument("--output-dir", type=Path, default=Path("aspm-generated"))
    args = parser.parse_args()
    base = os.environ["ASPM_URL"].rstrip("/")
    address = urlsplit(base)
    if address.scheme != "https" and not (address.scheme == "http" and address.hostname in {"localhost", "127.0.0.1"}):
        msg = "Use HTTPS for remote ASPM; HTTP is allowed only for a local test."
        raise ValueError(msg)
    headers = {"Authorization": "ASPM " + os.environ["ASPM_TOKEN"], "Content-Type": "application/json"}
    deliveries = [json.loads(path.read_text(encoding="utf-8")) for path in args.deliveries]
    commits = {row["commit"] for row in deliveries}
    if len(commits) != 1:
        msg = "All delivery responses must belong to one commit."
        raise ValueError(msg)
    commit_id = commits.pop()
    expected = json.loads(os.environ.get("ASPM_EXPECTED_SCANNERS", '["Semgrep JSON Report","Trivy Scan"]'))

    def api(path, data=None, *, output=None):
        body = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request(base + "/api/aspm/v1" + path, data=body, headers=headers)  # noqa: S310 -- scheme checked above
        with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 -- scheme checked above
            if output is not None:
                with output.open("wb") as destination:
                    shutil.copyfileobj(response, destination, length=1024 * 1024)
                return None
            return json.load(response)

    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        scans = [api(f"/scans/{row['id']}/") for row in deliveries]
        if all(row["status"] in {"COMPLETED", "FAILED"} for row in scans):
            break
        time.sleep(2)
    else:
        msg = "Timed out waiting for scanner processing."
        raise TimeoutError(msg)
    scan_set = api(f"/commits/{commit_id}/finalize/", {"expected_scanners": expected})
    report = api(f"/commits/{commit_id}/reports/", {"scan_set_id": scan_set["id"]})
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        # Report lists are bounded, with after=<version> continuation.
        reports = api(f"/commits/{commit_id}/reports/?after={report['version'] - 1}")
        current = next(row for row in reports if row["id"] == report["id"])
        if current["status"] == "COMPLETED":
            break
        if current["status"] == "FAILED":
            msg = "ASPM report generation failed."
            raise RuntimeError(msg)
        time.sleep(2)
    else:
        msg = "Timed out waiting for ASPM report generation."
        raise TimeoutError(msg)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for output_format in ("html", "json"):
        api(f"/reports/{report['id']}/download/?format={output_format}", output=args.output_dir / f"report-v{report['version']}.{output_format}")
    print(json.dumps({"report_id": report["id"], "version": report["version"], "complete": current["manifest"]["complete"], "checksums": current["checksums"]}))
    if not current["manifest"]["complete"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
