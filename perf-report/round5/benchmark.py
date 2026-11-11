#!/usr/bin/env python3
"""Bounded mixed API benchmark. Pass a JSON list of credential objects on stdin.

Each object requires token, product and finding. For example, run
credential_provider | python3 mixed_load.py --concurrency 5 --requests 240 --output run.json
The output contains aggregate measurements and anonymized request timings; no credentials. An optional stop file ends the run.
"""

import argparse
import concurrent.futures
import http.client
import itertools
import json
import math
import random
import statistics
import sys
import threading
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

MIX = (
    ("findings", 6), ("filtered_product", 3), ("finding_detail", 2),
    ("products", 2), ("tests", 2), ("engagements", 1),
    ("dashboard", 2), ("web_products", 1), ("endpoints", 1),
)



def summarize(samples, elapsed):
    timings = sorted(item[0] for item in samples if item[1] == "200")

    def percentile(q):
        return round(timings[math.ceil(q * len(timings)) - 1], 3) if timings else None

    return {
        "requests": len(samples),
        "statuses": dict(Counter(item[1] for item in samples)),
        "error_rate": 1 - len(timings) / len(samples) if samples else None,
        "p50_ms": round(statistics.median(timings), 3) if timings else None,
        "p90_ms": percentile(0.90) if len(timings) >= 10 else None,
        "p95_ms": percentile(0.95) if len(timings) >= 20 else None,
        "p99_ms": percentile(0.99) if len(timings) >= 300 else None,
        "rps": round(len(samples) / elapsed, 3),
        "bytes": sum(item[3] for item in samples),
    }


def run(args, credentials):
    target = urlsplit(args.url)
    if target.scheme != "http" or target.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("The benchmark requires a local HTTP target")
    rng = random.Random(args.seed)
    scenarios = json.loads(args.scenarios.read_text())
    mix = MIX if args.scenario == "mixed" else ((args.scenario, 20),)
    cases = [(name, scenarios[name]["url"]) for name, weight in mix for _ in range(weight)] * (args.requests // 20)
    rng.shuffle(cases)
    actors = list(range(len(credentials))) * math.ceil(len(cases) / len(credentials))
    rng.shuffle(actors)
    stop = threading.Event()

    def execute(schedule, limit, phase):
        start = time.monotonic()
        deadline = start + limit
        if args.fixed_users:
            assigned = list(schedule)
            per_worker = [iter(assigned[i::args.concurrency]) for i in range(args.concurrency)]
            tasks = None
        else:
            tasks = iter(schedule)
        task_lock = threading.Lock()
        health = Counter()
        next_index = itertools.count()

        def worker(worker_index):
            connection = http.client.HTTPConnection(target.hostname, target.port, timeout=args.timeout)
            samples = []
            try:
                while not stop.is_set() and time.monotonic() < deadline:
                    if args.stop_file and args.stop_file.exists():
                        stop.set()
                        break
                    with task_lock:
                        task = next(per_worker[worker_index] if args.fixed_users else tasks, None)
                        request_index = next(next_index)
                    if task is None:
                        break
                    (case, template), actor = task
                    if args.fixed_users:
                        actor = worker_index % len(credentials)
                    credential = credentials[actor]
                    started = time.monotonic()
                    wall = time.time()
                    size = 0
                    sql_count = None
                    sql_ms = None
                    try:
                        path = template.format(**credential, nonce=f"s{args.seed}-c{args.concurrency}-{phase}-{request_index}")
                        headers = {"Accept": "application/json" if scenarios[case]["auth"] == "token" else "text/html"}
                        if scenarios[case]["auth"] == "token":
                            headers["Authorization"] = "Token " + credential["token"]
                        else:
                            headers["Cookie"] = "sessionid=" + credential["session"]
                        connection.request("GET", path, headers=headers)
                        response = connection.getresponse()
                        size = len(response.read())
                        status = str(response.status)
                        sql_header = response.getheader("X-Perf-SQL-Count")
                        sql_count = int(sql_header) if sql_header is not None else None
                        sql_header_ms = response.getheader("X-Perf-SQL-Ms")
                        sql_ms = float(sql_header_ms) if sql_header_ms is not None else None
                        if response.status == 200 and sql_count is None:
                            status = "missing_sql_metrics"
                    except (OSError, http.client.HTTPException) as error:
                        status = type(error).__name__
                        connection.close()
                    samples.append(((time.monotonic() - started) * 1000, status, case, size, actor, wall, sql_count, sql_ms))
                    with task_lock:
                        health["total"] += 1
                        health["errors"] += status != "200"
                        if health["errors"] >= 5 and health["errors"] / health["total"] >= 0.10:
                            stop.set()
                            if args.stop_file:
                                args.stop_file.touch()
                    if args.think_time:
                        time.sleep(args.think_time)
            finally:
                connection.close()
            return samples

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            samples = list(itertools.chain.from_iterable(executor.map(
                worker, range(args.concurrency),
            )))
        return samples, time.monotonic() - start

    warmup_cases = [(name, scenarios[name]["url"]) for name, weight in mix for _ in range(weight)]
    warmup = [(warmup_cases[index % 20], index % len(credentials)) for index in range(args.warmup)]
    _, _ = execute(warmup, min(args.seconds, 90), "warmup")
    start = time.time()
    samples, elapsed = execute(zip(cases, actors), args.seconds, "measure")
    if args.timeline:
        with args.timeline.open("w") as stream:
            for latency, status, case, _, _, wall, _, _ in sorted(samples, key=lambda row: row[5]):
                stream.write(json.dumps({"at":wall, "latency_ms":latency, "status":status, "case":case})+"\n")
    result = summarize(samples, elapsed)
    result.update(
        concurrency=args.concurrency, configured_users=len(credentials),
        observed_users=len({item[4] for item in samples}), scheduled_requests=args.requests,
        elapsed_s=round(elapsed, 3), started_at=start, ended_at=time.time(),
        variant=args.variant, scenario=args.scenario, think_time=args.think_time, fixed_users=args.fixed_users, seed=args.seed, stopped=stop.is_set() or len(samples) != args.requests,
        by_case={name: summarize([item for item in samples if item[2] == name], elapsed)
                 for name, _ in mix},
    )
    result["samples"] = [{"ms": round(row[0], 3), "status": row[1], "case": row[2], "bytes": row[3], "actor": row[4], "at": row[5], "sql_count": row[6], "sql_ms": row[7]} for row in samples]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:48085")
    parser.add_argument("--scenarios", type=Path, default=Path(__file__).with_name("scenarios.json"))
    parser.add_argument("--scenario", default="mixed")
    parser.add_argument("--think-time", type=float, default=0)
    parser.add_argument("--fixed-users", action="store_true")
    parser.add_argument("--admin-only", action="store_true")
    parser.add_argument("--variant", default="after")
    parser.add_argument("--concurrency", type=int, required=True)
    parser.add_argument("--requests", type=int, default=240)
    parser.add_argument("--warmup", type=int, default=25)
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--seed", type=int, default=35100)
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeline", type=Path)
    args = parser.parse_args()
    if not 1 <= args.concurrency <= 25 or args.requests <= 0 or args.requests % 20:
        parser.error("Concurrency must be 1–25 and requests must be a positive multiple of 20")
    if args.warmup < 0 or args.seconds <= 0 or args.timeout <= 0:
        parser.error("Warmup must be nonnegative and both time limits must be positive")
    credentials = json.load(sys.stdin)
    if not credentials or len({row["token"] for row in credentials}) != len(credentials):
        parser.error("Provide a nonempty list of distinct credentials")
    if args.admin_only:
        credentials = credentials[:1]
    result = run(args, credentials)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        f"c={args.concurrency} users={result['observed_users']} requests={result['requests']} "
        f"p95={result['p95_ms']}ms rps={result['rps']} statuses={result['statuses']}",
        flush=True,
    )
    return 1 if result["stopped"] or result["error_rate"] else 0


if __name__ == "__main__":
    sys.exit(main())
