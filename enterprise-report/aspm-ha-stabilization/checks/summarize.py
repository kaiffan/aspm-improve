"""Summarize completed qualification captures without credentials."""
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

raw = Path(__file__).resolve().parent.parent / "raw"


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def unix(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def availability(number, phases):
    label = f"rollout-{number}"
    tls = records(raw / f"{label}-tls.jsonl")
    internal = records(raw / f"{label}-clusterip.jsonl")
    plain = [row for row in tls if row.get("mode") == "raw"]
    retries = [row for row in tls if row.get("mode") == "retry"]
    cluster = [row for row in internal if "status" in row]
    downloads = [row for row in tls if row.get("mode") == "in_flight"]
    snapshots = []
    for line in (raw / f"{label}-endpoints.txt").read_text().splitlines():
        if re.match(r"^\d{4}-\d\d-\d\dT", line):
            at = unix(line)
            snapshots.append((at, []))
        elif line.strip():
            snapshots[-1][1].append(line)

    started = phases[f"{label}-start"]
    if f"{label}-ready" not in phases:
        return None
    settled = phases[f"{label}-ready"]
    active = [(at, rows) for at, rows in snapshots if at >= started]
    terminating = [at for at, rows in active if any("serving=true terminating=true" in line for line in rows)]
    ready_min = min(sum("ready=true" in line for line in rows) for _, rows in active)
    errors = Counter(str(row["attempts"][0]) for row in plain if row["attempts"][0] != 200)
    css = Counter(row["sha256"] for row in tls if "sha256" in row and row.get("path") == "/static/dojo/css/aspm.css")
    return {
        "raw_tls_count": len(plain),
        "raw_tls_errors": dict(errors),
        "retry_clients": len(retries),
        "retry_first_errors": sum(row["attempts"][0] != 200 for row in retries),
        "retry_final_errors": sum(row["attempts"][-1] != 200 for row in retries),
        "retry_total_attempts": sum(len(row["attempts"]) for row in retries),
        "clusterip_count": len(cluster),
        "clusterip_errors": dict(Counter(str(row.get("error", row["status"])) for row in cluster if row["status"] != 200)),
        "first_serving_terminating_epoch": min(terminating, default=None),
        "min_ready_endpoints": ready_min,
        "rollout_ready_seconds": settled - started,
        "download": downloads[0] if downloads else None,
        "static_asset_checksums": dict(css),
    }


def peaks(samples, start, end):
    scope = [row for row in samples if start <= row["at"] <= end]
    if not scope:
        return {"samples": 0}
    return {
        "from": start,
        "to": end,
        "samples": len(scope),
        **{label: max(row[label] for row in scope) for label in ("total", "active", "waiting_lock", "idle_in_transaction")},
    }


def generate():
    phases = {}
    for line in (raw / "phase-timestamps.txt").read_text().splitlines():
        epoch, event = line.split()
        phases[event] = int(epoch)
    stages = {}
    samples = records(raw / "postgres-samples.jsonl")

    def stage(name, start, end):
        stages[name] = peaks(samples, start, end)

    for label in ("a-closed", "a-fixed", "b-closed", "b-fixed", "web-budget-closed", "web-budget-fixed",
                  "worker-1", "worker-2", "worker-3", "worker-replacement", "mixed", "webhook"):
        if f"{label}-end" in phases:
            stage(label, phases[f"{label}-start"], phases[f"{label}-end"])
    if "matched-scale-up" in phases:
        stage("matched-scale-up", phases["matched-scale-up"], phases["b-closed-start"])
    if "worker-rescale-start" in phases and "worker-3-end" in phases:
        stage("worker-rescale", phases["worker-rescale-start"], phases["worker-3-end"])
    app_rollouts = {}
    for number in range(1, 8):
        name = f"rollout-{number}"
        if f"{name}-ready" in phases:
            app_rollouts[name] = availability(number, phases)
            stage(name, phases[f"{name}-start"], phases[f"{name}-ready"])
    for number in (1, 2, 3):
        result = raw / f"worker-{number}" / "ingestion-recovery.json"
        if result.exists() and result.stat().st_size:
            try:
                report = json.loads(result.read_text())["report"]
            except json.JSONDecodeError:
                continue
            if "requested_at" in report:
                stage(f"report-{number}", report["requested_at"], report["complete_observed_at"])
    if (raw / "migration-events.txt").exists():
        starts = []
        ends = []
        for line in (raw / "migration-events.txt").read_text().splitlines():
            start, end, event, *_ = line.split()
            if event == "SuccessfulCreate":
                starts.append(unix(start))
            elif event == "Completed":
                ends.append(unix(end))
        for i, (start, end) in enumerate(zip(sorted(starts), sorted(ends), strict=True), start=1):
            stage(f"migration-{i}", start, end)
    stage("all", samples[0]["at"], samples[-1]["at"])
    return {"rollouts": app_rollouts, "postgres": stages}


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2))
