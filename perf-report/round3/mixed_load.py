#!/usr/bin/env python3
"""Bounded mixed API benchmark. Pass a JSON list of credential objects on stdin.

Each object requires token, product and finding. For example, run
credential_provider | python3 mixed_load.py --concurrency 5 --requests 240 --output run.json
The output contains aggregate measurements only. An optional stop file ends the run.
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
    ("findings", 8, "/api/v2/findings/?limit=100"),
    ("filtered", 4, "/api/v2/findings/?product={product}&severity=High&active=true&limit=100"),
    ("finding_detail", 3, "/api/v2/findings/{finding}/"),
    ("product_count", 2, "/api/v2/products/?findings=count"),
    ("tests", 2, "/api/v2/tests/"),
    ("engagements", 1, "/api/v2/engagements/"),
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
    cases = [(name, url) for name, weight, url in MIX for _ in range(weight)] * (args.requests // 20)
    rng.shuffle(cases)
    actors = list(range(len(credentials))) * math.ceil(len(cases) / len(credentials))
    rng.shuffle(actors)
    stop = threading.Event()

    def execute(schedule, limit):
        start = time.monotonic()
        deadline = start + limit
        tasks = iter(schedule)
        task_lock = threading.Lock()
        health = Counter()

        def worker():
            connection = http.client.HTTPConnection(target.hostname, target.port, timeout=args.timeout)
            samples = []
            try:
                while not stop.is_set() and time.monotonic() < deadline:
                    if args.stop_file and args.stop_file.exists():
                        stop.set()
                        break
                    with task_lock:
                        task = next(tasks, None)
                    if task is None:
                        break
                    (case, template), actor = task
                    credential = credentials[actor]
                    started = time.monotonic()
                    wall = time.time() if args.timeline else None
                    size = 0
                    try:
                        path = template.format(product=credential["product"], finding=credential["finding"])
                        connection.request("GET", path, headers={
                            "Accept": "application/json",
                            "Authorization": "Token " + credential["token"],
                            "X-DD-Perf-Variant": args.variant,
                        })
                        response = connection.getresponse()
                        size = len(response.read())
                        status = str(response.status)
                    except (OSError, http.client.HTTPException) as error:
                        status = type(error).__name__
                        connection.close()
                    samples.append(((time.monotonic() - started) * 1000, status, case, size, actor, wall))
                    with task_lock:
                        health["total"] += 1
                        health["errors"] += status != "200"
                        if health["errors"] >= 5 and health["errors"] / health["total"] >= 0.10:
                            stop.set()
            finally:
                connection.close()
            return samples

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            samples = list(itertools.chain.from_iterable(executor.map(
                lambda _: worker(), range(args.concurrency),
            )))
        return samples, time.monotonic() - start

    warmup_cases = [(name, url) for name, weight, url in MIX for _ in range(weight)]
    warmup = [(warmup_cases[index % 20], index % len(credentials)) for index in range(args.warmup)]
    _, _ = execute(warmup, min(args.seconds, 45))
    start = time.time()
    samples, elapsed = execute(zip(cases, actors), args.seconds)
    if args.timeline:
        with args.timeline.open("w") as stream:
            for latency, status, case, _, _, wall in sorted(samples, key=lambda row: row[5]):
                stream.write(json.dumps({"at":wall, "latency_ms":latency, "status":status, "case":case})+"\n")
    result = summarize(samples, elapsed)
    result.update(
        concurrency=args.concurrency, configured_users=len(credentials),
        observed_users=len({item[4] for item in samples}), scheduled_requests=args.requests,
        elapsed_s=round(elapsed, 3), started_at=start, ended_at=time.time(),
        seed=args.seed, stopped=stop.is_set() or len(samples) != args.requests,
        by_case={name: summarize([item for item in samples if item[2] == name], elapsed)
                 for name, _, _ in MIX},
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:48081")
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
