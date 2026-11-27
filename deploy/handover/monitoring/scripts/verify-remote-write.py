"""Verify WAL recovery and alert resolution on the explicitly named OrbStack lab."""
# ruff: noqa: INP001
import json
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

NAMESPACE = "aspm-lab-monitoring"
KUBECTL = ["kubectl", "--context", "orbstack", "-n", NAMESPACE]
PROMETHEUS = "http://127.0.0.1:19090"
SELECTOR = 'up{application="aspm",namespace="aspm-lab-monitoring",component="web"}'
ALERT = "ASPMRemoteWriteStalled"


def query(endpoint, expr=None):
    if expr:
        endpoint += "?" + urllib.parse.urlencode({"query": expr})
    with urllib.request.urlopen(PROMETHEUS + endpoint, timeout=5) as response:
        return json.load(response)["data"]


def vm_query(expr):
    vm_args = ["curl", "--silent", "--show-error", "--fail", "--max-time", "8",
               "--cacert", str(Path.cwd() / "ca.crt"), "--resolve", "vm-monitor:18428:127.0.0.1",
               "https://vm-monitor:18428/api/v1/query", "--get", "--data-urlencode", "query=" + expr]
    return json.loads(subprocess.check_output(vm_args))["data"]["result"]


def wait_for(probe, *, seconds=125):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if result := probe():
            return result
        time.sleep(4)
    msg = "Timed out waiting for telemetry recovery condition"
    raise TimeoutError(msg)


def alert_is_firing():
    return any(item["labels"]["alertname"] == ALERT and item["state"] == "firing" for item in query("/api/v1/alerts")["alerts"])


def retry_count():
    result = query("/api/v1/query", 'sum(prometheus_remote_storage_samples_retried_total{remote_name="aspm-victoriametrics"})')["result"]
    return float(result[0]["value"][1]) if result else 0


def kubectl(*args):
    subprocess.run([*KUBECTL, *args], check=True, stdout=subprocess.DEVNULL)


def main():
    assert len(vm_query(SELECTOR)) == 2
    assert not alert_is_firing()
    before = retry_count()
    try:
        kubectl("scale", "deployment/vm-monitor", "--replicas=0")
        began = time.time()
        wait_for(alert_is_firing)
        during = retry_count()
        assert during > before
    finally:
        restored = time.time()
        kubectl("scale", "deployment/vm-monitor", "--replicas=1")
        kubectl("rollout", "status", "deployment/vm-monitor", "--timeout=60s")
    with subprocess.Popen([*KUBECTL, "port-forward", "--address", "127.0.0.1", "svc/vm-monitor", "18429:8428"],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proxy:
        try:
            assert proxy.stdout.readline().startswith("Forwarding from")
            # Curl still verifies the certificate for vm-monitor while using the replacement tunnel.
            def samples_in_outage():
                args = ["curl", "--silent", "--show-error", "--fail", "--max-time", "8",
                        "--cacert", str(Path.cwd() / "ca.crt"), "--resolve", "vm-monitor:18429:127.0.0.1",
                        "https://vm-monitor:18429/api/v1/query", "--get", "--data-urlencode", "query=" + SELECTOR + "[10m]"]
                series = json.loads(subprocess.check_output(args))["data"]["result"]
                counts = [sum(began + 5 < float(stamp) < restored - 2 for stamp, _ in value["values"]) for value in series]
                return counts if len(counts) == 2 and min(counts) >= 2 else None

            counts = wait_for(samples_in_outage, seconds=60)
            wait_for(lambda: not alert_is_firing(), seconds=90)
        finally:
            proxy.terminate()
    print(json.dumps({"outage_seconds": round(restored - began, 1), "retried_samples_delta": during - before,
                      "backfilled_samples_per_web_target": counts, "alert": ALERT, "fired": True, "resolved": True}, indent=2))


if __name__ == "__main__":
    main()
