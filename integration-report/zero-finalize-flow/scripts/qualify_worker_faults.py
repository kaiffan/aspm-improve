"""Host controller: real broker stop and worker SIGKILL, restricted to this task's containers."""
# ruff: noqa: INP001, T201, S101, PT018
import json
import shutil
import subprocess
import sys
import time

if sys.flags.optimize:
    msg = "Qualification requires Python assertions enabled."
    raise RuntimeError(msg)

DOCKER = shutil.which("docker")
assert DOCKER

HTTP = "aspm-zero-runtime-http-1"
WORKER = "aspm-zero-runtime-worker-1"
BROKER = "aspm-zero-runtime-runtime-broker-1"
for container in (HTTP, WORKER, BROKER):
    data = json.loads(subprocess.check_output([DOCKER, "inspect", container]))[0]
    assert data["Config"]["Labels"]["org.aspm.zero-finalize.owner"] == "aspm-zero-finalize"


def call(code, *, django=False):
    command = [DOCKER, "exec", HTTP, "python"]
    command += ["manage.py", "shell", "-c", code] if django else ["-c", code]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return next(json.loads(line) for line in reversed(result.stdout.splitlines()) if line.startswith("{"))


def upload(key, count):
    return call("""import requests,json
from pathlib import Path
c=json.loads(Path('/zero-runtime/credentials.json').read_text(encoding="utf-8"))
payload=json.dumps({'findings':[{'title':f'Worker fault finding {i}','description':'Synthetic restart fixture','severity':'High'} for i in range(""" + str(count) + """)]}).encode()
r=requests.post('http://127.0.0.1:8080/api/aspm/v1/scans/',headers={'Authorization':'ASPM '+c['token']},data={'project_id':c['product_id'],'repository_id':c['repository_id'],'commit_sha':'a'*40,'scanner_type':'Generic Findings Import','idempotency_key':""" + repr(key) + """,'pipeline_id':c['run'],'job_id':'fault-fixture','scan_scope':""" + repr(key) + """},files={'file':('fault.json',payload,'application/json')},timeout=90)
assert r.status_code==202,(r.status_code,r.text[:300])
print(json.dumps(r.json()))""")


def state(identifier):
    return call("from dojo.aspm_ingestion.models import ScanRun,IngestionJob; import json; s=ScanRun.objects.get(pk=" + repr(identifier) + "); print(json.dumps({'status':s.status,'attempt':s.attempt,'test':s.test_id,'count':s.finding_count,'generation':s.observation_generation,'outbox':IngestionJob.objects.filter(scan=s).exists()}))", django=True)


def dispatch(identifier):
    return call("from dojo.aspm_ingestion.models import IngestionJob; from dojo.aspm_ingestion.tasks import dispatch_jobs; from django.utils import timezone; import json; IngestionJob.objects.filter(scan_id=" + repr(identifier) + ").update(next_dispatch_at=timezone.now()); dispatch_jobs(); print(json.dumps({'dispatched':True}))", django=True)


def wait(identifier, timeout=180):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        row = state(identifier)
        if row["status"] in {"COMPLETED", "FAILED"}:
            assert row["status"] == "COMPLETED", row
            return row
        time.sleep(.5)
    msg = "worker recovery"
    raise TimeoutError(msg)


nonce = str(int(time.time()))
subprocess.run([DOCKER, "stop", "-t", "1", BROKER], check=True, stdout=subprocess.DEVNULL)
try:
    scan = upload("broker-loss/" + nonce, 1)
    pending = state(scan["id"])
    assert pending["status"] == "ACCEPTED" and pending["outbox"]
finally:
    subprocess.run([DOCKER, "start", BROKER], check=True, stdout=subprocess.DEVNULL)
time.sleep(2)
dispatch(scan["id"])
broker_result = wait(scan["id"])
assert not broker_result["outbox"]
scan = upload("worker-kill/" + nonce, 3000)
deadline = time.monotonic() + 90
while time.monotonic() < deadline:
    before = state(scan["id"])
    if before["status"] == "PROCESSING" and before["test"]:
        break
    assert before["status"] != "COMPLETED", "Worker finished before the deliberate kill; preserve result and rerun with a larger bounded fixture"
    time.sleep(.1)
else:
    msg = "worker never entered import"
    raise TimeoutError(msg)
subprocess.run([DOCKER, "kill", "--signal=KILL", WORKER], check=True, stdout=subprocess.DEVNULL)
after_kill = state(scan["id"])
assert after_kill["status"] == "PROCESSING" and after_kill["outbox"]
subprocess.run([DOCKER, "start", WORKER], check=True, stdout=subprocess.DEVNULL)
time.sleep(2)
dispatch(scan["id"])
recovered = wait(scan["id"], timeout=240)
assert recovered["test"] == before["test"]
assert recovered["attempt"] >= 2 and recovered["count"] == 3000 and not recovered["outbox"]
print(json.dumps({"passed": True, "broker_loss": {"accepted_during_outage": pending, "recovered": broker_result},
                  "worker_sigkill": {"before": before, "after_kill": after_kill, "recovered": recovered},
                  "scope": "owned local containers; actual broker outage and SIGKILL; immediate dispatcher retry scheduling only for the two synthetic jobs"}))
