# ruff: noqa: INP001, S101, S310, T201
"""Local fault qualification: refuses to target a container outside the isolated API worktree."""

import json
import shutil
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path

c = json.loads(Path(".cache/api-runtime/credentials.json").read_text(encoding="utf-8"))
base = "http://127.0.0.1:48094/api/aspm/v1"
ns = uuid.uuid4().hex
container = "aspm-api-ingestion-uwsgi-1"
docker_binary = shutil.which("docker")
if docker_binary is None:
    msg = "Docker CLI is required."
    raise RuntimeError(msg)
mounts = json.loads(subprocess.check_output([docker_binary, "inspect", container, "--format", "{{json .Mounts}}"]))
assert any("/.cache/aspm-api-ingestion/dojo" in m.get("Source", "") for m in mounts), (
    "Refuse to inject faults outside the isolated API worktree"
)


def http(path, data=None, content_type=None, *, human=False):
    h = {"Cookie": "sessionid=" + c["session"]} if human else {"Authorization": "ASPM " + c["token"]}
    if content_type:
        h["Content-Type"] = content_type
    with urllib.request.urlopen(urllib.request.Request(base + path, data=data, headers=h), timeout=180) as r:
        return json.load(r)


report = json.dumps(
    {
        "findings": [
            {
                "title": f"Worker recovery {ns} {i}",
                "description": "Synthetic worker death qualification",
                "severity": "High",
                "cwe": 79,
            }
            for i in range(4000)
        ],
    },
).encode()
boundary = "aspm-" + ns
fields = {
    "project_id": c["product_id"],
    "repository_url": "https://github.com/example/worker-recovery",
    "commit_sha": "d" * 40,
    "scanner_type": "Generic Findings Import",
    "idempotency_key": "worker-fault/" + ns,
}
body = (
    b"".join(
        f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items()
    )
    + f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="scan.json"\r\n\r\n'.encode()
    + report
    + f"\r\n--{boundary}--\r\n".encode()
)
scan = http("/scans/", body, "multipart/form-data; boundary=" + boundary)
identifier = scan["id"]
killed = []
test_id = None
for _failure in range(3):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        code = 'import json; from dojo.celery import app; print("ACTIVE:"+json.dumps(app.control.inspect(timeout=0.5).active() or {}))'
        output = subprocess.check_output(
            [
                docker_binary,
                "exec",
                "-e",
                "DD_CELERY_BROKER_URL=redis://valkey:6379/4",
                "-e",
                "DD_CACHE_URL=redis://valkey:6379/5",
                container,
                "python",
                "manage.py",
                "shell",
                "-c",
                code,
            ],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        tasks = json.loads(next(line[7:] for line in output.splitlines() if line.startswith("ACTIVE:")))
        task = next(
            (
                t
                for values in tasks.values()
                for t in values
                if t["name"] == "dojo.aspm_ingestion.process_job" and identifier in str(t["args"])
            ),
            None,
        )
        if task:
            state = http("/scans/" + identifier + "/", human=True)
            if test_id is None:
                test_id = state["test"]
            pid = int(task["worker_pid"])
            assert pid > 1
            kill_code = 'import os,signal,sys,pathlib; p=int(sys.argv[1]); assert b"celery" in pathlib.Path("/proc",str(p),"cmdline").read_bytes(); os.kill(p,signal.SIGKILL)'
            subprocess.run([docker_binary, "exec", container, "python", "-c", kill_code, str(pid)], check=True)
            killed.append({"worker_pid": pid, "attempt": state["attempt"], "test_id": state["test"]})
            break
        time.sleep(0.2)
    else:
        msg = "No matching isolated worker task found"
        raise TimeoutError(msg)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        state = http("/scans/" + identifier + "/", human=True)
        if state["status"] == "FAILED" or state["attempt"] > killed[-1]["attempt"]:
            break
        time.sleep(0.1)
deadline = time.monotonic() + 120
while time.monotonic() < deadline:
    state = http("/scans/" + identifier + "/", human=True)
    if state["status"] == "FAILED":
        break
    time.sleep(0.2)
assert state["status"] == "FAILED", state["status"]
assert state["error_code"] == "worker_recovery_limit", state["error_code"]
failed = dict(state)
http("/scans/" + identifier + "/retry/", b"{}", "application/json")
deadline = time.monotonic() + 180
while time.monotonic() < deadline:
    state = http("/scans/" + identifier + "/", human=True)
    if state["status"] in {"COMPLETED", "FAILED"}:
        break
    time.sleep(0.5)
assert state["status"] == "COMPLETED", state["error_code"]
assert state["finding_count"] == 4000, state["finding_count"]
assert state["test"] == test_id, (state["test"], test_id)
result = {
    "scan_id": identifier,
    "worker_deaths": killed,
    "failed_status": failed["status"],
    "failed_code": failed["error_code"],
    "final_status": state["status"],
    "final_attempt": state["attempt"],
    "finding_count": state["finding_count"],
    "test_id": state["test"],
    "same_reserved_test": True,
    "timings": state["timings"],
}
Path("perf-report/aspm-api/worker-recovery.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
