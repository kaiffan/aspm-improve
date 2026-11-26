# ruff: noqa
# Preserved qualification harness; source hashes are in input/harness-provenance.json.
"""Real HTTP workflow driver with bounded payloads, raw timings and semantic checks."""

import concurrent.futures
import csv
import hashlib
import http.client
import io
import json
import math
import random
import statistics
import threading
import time
import urllib.parse

import lab

LIMIT = 33554432


def summary(rows, elapsed):
    valid = [r for r in rows if r.get("valid")]
    values = sorted(r["ms"] for r in valid)
    n = len(values)

    def q(f, min_n):
        return values[math.ceil(n * f) - 1] if n >= min_n else None

    return {
        "n": len(rows),
        "valid": n,
        "errors": len(rows) - n,
        "p50_ms": q(0.5, 1),
        "p90_ms": q(0.9, 100),
        "p95_ms": q(0.95, 100),
        "p99_ms": q(0.99, 300),
        "mean_ms": statistics.mean(values) if values else None,
        "min_ms": min(values) if values else None,
        "max_ms": max(values) if values else None,
        "rps": len(rows) / elapsed if elapsed else None,
        "elapsed_s": elapsed,
        "tail_policy": "p90/p95 withheld below100valid; p99 below300; errors never removed from raw",
    }


class Driver:
    def __init__(self, label, stop=None):
        self.owner = lab.load()
        self.label = label
        self.stop = stop or threading.Event()
        self.identities = json.loads((lab.PRIVATE / "identities.json").read_text())
        self.accounts = self.identities["accounts"]
        self.lock = threading.Lock()
        self.inflight = 0
        self.max_inflight = 0
        self.http = []
        self.events = []
        self.errors = 0
        self.consecutive_5xx = 0
        self.raw = lab.OUT / "raw" / (label + ".http.jsonl")
        self.raw.parent.mkdir(parents=True, exist_ok=True)
        self.telemetry_offsets = {}
        self.tasks = {}
        self.last_publish = {}

    def account(self, i):
        return self.accounts[i % len(self.accounts)]

    def context(self, i, actor=None):
        actor = actor or self.account(i)
        product = actor["products"][0]
        test = (product - 1) * 1250 + (i * 137) % 1250 + 1
        return {
            "product": product,
            "test": test,
            "engagement": (test - 1) // 250 + 1,
            "finding": (test - 1) * 400 + (i % 5) + 1,
            "anchor": (test - 1) * 400 + 1,
        }

    def request(
        self,
        actor,
        method,
        path,
        body=None,
        expected=(200,),
        op=None,
        content_type="application/json",
        redirects=True,
        extra_headers=None,
    ):
        if self.stop.is_set():
            raise RuntimeError("Resource/business stop flag set")
        payload = (
            body
            if isinstance(body, bytes)
            else json.dumps(body).encode()
            if body is not None
            else None
        )
        headers = {
            "Accept": "*/*",
            "X-Acceptance-Operation": op or self.label,
            "Content-Type": content_type,
        }
        if actor.get("token"):
            headers["Authorization"] = "Token " + actor["token"]
        # API writes use Token auth without a competing SessionAuthentication cookie.
        # Read baseline keeps its existing session/header behavior; UI writes carry real CSRF.
        if actor.get("session") and (method == "GET" or not path.startswith("/api/")):
            headers["Cookie"] = "sessionid=" + actor["session"]
        if extra_headers:
            headers.update(extra_headers)
        initial_method = method
        initial_bytes = len(payload or b"")
        start = time.perf_counter()
        at = time.time()
        current = path
        chain = []
        status = None
        data = b""
        rh = {}
        error = None
        send_ms = None
        ttfb_ms = None
        with self.lock:
            self.inflight += 1
            self.max_inflight = max(self.max_inflight, self.inflight)
            self.events.append({"at": at, "http_inflight": self.inflight})
        try:
            for _ in range(6):
                c = http.client.HTTPConnection(
                    "127.0.0.1", self.owner["port"], timeout=90
                )
                try:
                    sent = time.perf_counter()
                    c.request(method, current, body=payload, headers=headers)
                    send_ms = (time.perf_counter() - sent) * 1000
                    r = c.getresponse()
                    ttfb_ms = (time.perf_counter() - sent) * 1000
                    status = r.status
                    rh = {k.lower(): v for k, v in r.getheaders()}
                    parts = []
                    size = 0
                    while True:
                        chunk = r.read(65536)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > LIMIT:
                            raise RuntimeError(
                                "Response size guard >32MiB; partial invalid observation preserved"
                            )
                        parts.append(chunk)
                    data = b"".join(parts)
                finally:
                    c.close()
                chain.append({"path": current, "status": status, "bytes": len(data)})
                if (
                    redirects
                    and status in [301, 302, 303, 307, 308]
                    and "location" in rh
                ):
                    u = urllib.parse.urlsplit(rh["location"])
                    if u.netloc and u.hostname not in ["127.0.0.1", "localhost"]:
                        raise RuntimeError("External redirect rejected")
                    current = u.path + ("?" + u.query if u.query else "")
                    if current.startswith("/login") and not path.startswith("/login"):
                        raise RuntimeError("Not authenticated: redirected to login")
                    if status == 303 or (status in [301, 302] and method == "POST"):
                        method = "GET"
                        payload = None
                    continue
                break
            if status not in expected:
                raise RuntimeError(f"Unexpected HTTP {status}; expected {expected}")
            valid = True
        except Exception as exc:
            error = str(exc)
            valid = False
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            row = {
                "at": at,
                "ended_at": time.time(),
                "label": self.label,
                "opid": op or self.label,
                "method": initial_method,
                "path": path,
                "status": status,
                "expected_status": list(expected),
                "valid": valid,
                "error": error,
                "ms": elapsed,
                "request_bytes": initial_bytes,
                "actual_http_requests": len(chain),
                "all_response_bytes": sum(x["bytes"] for x in chain),
                "response_bytes": len(data),
                "response_sha256": hashlib.sha256(data).hexdigest(),
                "send_ms": send_ms,
                "ttfb_ms": ttfb_ms,
                "sql_count": int(rh["x-acceptance-sql-count"])
                if rh.get("x-acceptance-sql-count")
                else None,
                "sql_ms": float(rh["x-acceptance-sql-ms"])
                if rh.get("x-acceptance-sql-ms")
                else None,
                "django_ms": float(rh["x-acceptance-view-ms"])
                if rh.get("x-acceptance-view-ms")
                else None,
                "redirect_chain": chain,
            }
            with self.lock:
                self.inflight -= 1
                self.events.append({"at": time.time(), "http_inflight": self.inflight})
                self.http.append(row)
                with self.raw.open("a") as out:
                    out.write(json.dumps(row) + "\n")
                if not valid:
                    self.errors += 1
                self.consecutive_5xx = (
                    self.consecutive_5xx + 1 if status and status >= 500 else 0
                )
                if self.consecutive_5xx >= 3 or (
                    len(self.http) >= 20 and self.errors / len(self.http) > 0.05
                ):
                    self.stop.set()
        return {
            "status": status,
            "data": data,
            "headers": rh,
            "observation": row,
            "valid": valid,
        }

    def json(self, *args, **kwargs):
        r = self.request(*args, **kwargs)
        if not r["valid"]:
            raise RuntimeError(r["observation"]["error"])
        return json.loads(r["data"]), r

    def read(self, case, index):
        actor = (
            self.identities["operator"]
            if case.get("actor") == "operator"
            else self.account(index)
        )
        ctx = self.context(index, self.account(index))
        url = case["url"].format(**ctx)
        op = f"{self.label}:{case['id']}:{index}"
        r = self.request(
            actor, "GET", url, expected=tuple(case["expected_status"]), op=op
        )
        if not r["valid"]:
            raise RuntimeError(r["observation"]["error"])
        if case["format"] == "json":
            d = json.loads(r["data"])
            if isinstance(d, dict) and "results" in d:
                assert isinstance(d["results"], list)
                ids = [
                    x["id"] for x in d["results"] if isinstance(x, dict) and "id" in x
                ]
                assert len(ids) == len(set(ids))
                if case["id"] == "products_full":
                    for product in d["results"]:
                        assert product["findings_count"] == len(
                            product["findings_list"]
                        )
                if case["id"] == "findings_sort_title":
                    assert [x["title"] for x in d["results"]] == sorted(
                        x["title"] for x in d["results"]
                    )
                if case["id"] == "v3_findings_cursor":
                    assert d["count"] is None
            if case["id"] in ["finding_detail", "v3_finding_detail"]:
                assert d["id"] == ctx["finding"]
        elif case["format"] == "html":
            assert b"<html" in r["data"].lower() and b"</html>" in r["data"].lower()
            if case["id"] == "ui_finding":
                assert (
                    b"finding-title" in r["data"]
                    and b"Deterministic finding" in r["data"]
                )
        elif case["format"] == "csv":
            rows = list(csv.reader(io.StringIO(r["data"].decode("utf-8-sig"))))
            assert len(rows) == 401
        return {
            "case": case["id"],
            "valid": True,
            "ms": r["observation"]["ms"],
            "response_bytes": len(r["data"]),
            "sql_ms": r["observation"]["sql_ms"],
            "sql_count": r["observation"]["sql_count"],
        }

    def telemetry(self):
        with self.lock:
            for file in (lab.PRIVATE / "telemetry").glob("*.jsonl"):
                offset, pending = self.telemetry_offsets.get(str(file), (0, ""))
                with file.open() as f:
                    f.seek(offset)
                    chunk = f.read()
                    offset = f.tell()
                lines = (pending + chunk).split("\n")
                pending = lines.pop()
                self.telemetry_offsets[str(file)] = (offset, pending)
                for line in lines:
                    if not line:
                        continue
                    row = json.loads(line)
                    if row.get("database") != self.owner[
                        "active_database"
                    ] or not row.get("task_id"):
                        continue
                    task = self.tasks.setdefault(row["task_id"], {})
                    if row.get("opid"):
                        task["opid"] = row["opid"]
                    if row["event"] == "task_publish":
                        task["published"] = row["at"]
                        self.last_publish[row.get("opid")] = row["at"]
                    if row["event"] == "task_end":
                        task["state"] = row["state"]
                        task["ended"] = row["at"]

    def background(self, op, required=False):
        deadline = time.monotonic() + 240
        start = time.time()
        while time.monotonic() < deadline and not self.stop.is_set():
            self.telemetry()
            tasks = [x for x in self.tasks.values() if x.get("opid") == op]
            if any(t.get("state") == "FAILURE" for t in tasks):
                raise RuntimeError("Real Celery task FAILURE")
            if (
                (tasks or not required)
                and all(t.get("state") == "SUCCESS" for t in tasks)
                and time.time() - self.last_publish.get(op, start) > 0.3
            ):
                return len(tasks)
            time.sleep(0.1)
        raise RuntimeError("Actual background completion not confirmed within240s")


def run_reads(label, cases, concurrency, requests, seconds=300, think_ms=0):
    lab.host(label)
    assert not lab.load()["diagnostic"], "No deep instrumentation in baseline"
    driver = Driver(label)
    from guards import Monitor

    monitor = Monitor(label, driver.stop).start()
    rng = random.Random(35100101)
    schedule = [cases[i % len(cases)] for i in range(requests)]
    rng.shuffle(schedule)
    rows = []
    lock = threading.Lock()
    next_index = iter(range(requests))
    started = time.monotonic()
    start_cpu = time.process_time()
    deadline = started + seconds

    def worker(_):
        while not driver.stop.is_set() and time.monotonic() < deadline:
            with lock:
                i = next(next_index, None)
            if i is None:
                return
            start = time.perf_counter()
            at = time.time()
            try:
                result = driver.read(schedule[i], i)
            except Exception as exc:
                if isinstance(exc, AssertionError):
                    driver.stop.set()
                result = {
                    "case": schedule[i]["id"],
                    "valid": False,
                    "ms": (time.perf_counter() - start) * 1000,
                    "error": str(exc),
                }
            result.update(index=i, at=at, ended_at=time.time())
            with lock:
                rows.append(result)
                with (lab.OUT / "raw" / (label + ".samples.jsonl")).open("a") as f:
                    f.write(json.dumps(result) + "\n")
            if think_ms:
                time.sleep(think_ms / 1000)

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(worker, range(concurrency)))
    elapsed = time.monotonic() - started
    client_cpu = time.process_time() - start_cpu
    resources = monitor.finish()
    result = {
        "label": label,
        "concurrency": concurrency,
        "unique_users": min(10, requests),
        "model": "closedloopHTTPpool; notfixeduniqueVUs",
        "think_ms": think_ms,
        "requested": requests,
        "client_cpu_s": client_cpu,
        "max_http_inflight": driver.max_inflight,
        "stopped": driver.stop.is_set() or len(rows) != requests,
        "summary": summary(rows, elapsed),
        "by_case": {
            c["id"]: summary([r for r in rows if r["case"] == c["id"]], elapsed)
            for c in cases
        },
        "samples": rows,
        "http_concurrency": driver.events,
        "instrumentation": "minimalcounts/taskobserver; noSQLstack/cProfile duringbaseline",
        "resource_guard": resources,
    }
    lab.save(lab.OUT / "raw" / (label + ".json"), result)
    return result, driver
