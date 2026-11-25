"""Trace the actual authenticated evidence view with rollback-only synthetic fixtures."""
# ruff: noqa: INP001, T201, S101
import collections
import hashlib
import json
import math
import os
import resource
import statistics
import sys
import time
import traceback
from datetime import timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from dojo.aspm_ingestion.models import FindingObservation, ScanRun
from dojo.models import Product, Product_Type
from dojo.scm.models import Commit, Repository


def trace(rows):
    def capture(execute, sql, params, many, context):
        frames = [frame for frame in traceback.extract_stack() if "/dojo/" in frame.filename]
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            rows.append({"sql": sql, "params": params, "elapsed_ms": (time.perf_counter() - start) * 1000,
                         "callers": [f"{frame.filename.split('/dojo/', 1)[1]}:{frame.lineno}:{frame.name}" for frame in frames[-5:]]})
    return capture


def cpu_usec():
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_read_file('/sys/fs/cgroup/cpu.stat')")
        return int(dict(line.split() for line in cursor.fetchone()[0].splitlines())["usage_usec"])


def seed(repo, actor, label, count, mode, observations=1):
    commit = Commit.objects.create(repository=repo, sha=hashlib.sha1(label.encode(), usedforsecurity=False).hexdigest())
    now = timezone.now()
    scans = []
    complete = []
    expected = {}
    for i in range(count):
        status = "COMPLETED" if mode == "reruns" or i % 5 < 3 else ("PROCESSING" if i % 5 == 3 else "FAILED")
        scanner = "Semgrep JSON Report" if mode == "reruns" else ("Semgrep JSON Report", "Trivy Scan", "Gitleaks Scan")[i % 3]
        scope = "src" if mode in {"reruns", "large"} else f"scope-{i % 11}"
        pipeline = f"pipeline-{i % 3}" if mode == "mixed" else "pipeline-0"
        scan = ScanRun(product_id=repo.product_id, commit=commit, submitted_by=actor, delivery_key=f"{label}-{i}",
                       scanner=scanner, artifact_sha256="0"*64, fingerprint="1"*64, artifact_path="synthetic/none",
                       artifact_size=1, original_name="synthetic.json", observation_generation=1,
                       metadata={"pipeline_id":pipeline, "job_id":scanner, "scan_scope":scope, "attempt_number":i+1},
                       finished_at=now + timedelta(seconds=i) if status == "COMPLETED" else None,
                       started_at=now, status="PROCESSING" if status == "COMPLETED" else status,
                       finding_count=observations if status == "COMPLETED" else 0,
                       severity_summary={"High":observations} if status == "COMPLETED" else {})
        scans.append(scan)
        if status == "COMPLETED":
            complete.append(scan)
            if pipeline == "pipeline-0":
                expected[(scanner, scope)] = str(scan.id)
    ScanRun.objects.bulk_create(scans, batch_size=250)
    for scan in complete:
        FindingObservation.objects.bulk_create(
            (FindingObservation(scan=scan, generation=1, source_finding_id=index, identity=f"{index:064x}", severity="High",
                                snapshot={"title":f"Synthetic observation {index}", "severity":"High", "cwe":79, "vulnerability_ids":["CVE-2026-0000"]})
             for index in range(observations)), batch_size=500)
    ScanRun.objects.filter(pk__in=[scan.pk for scan in complete]).update(status="COMPLETED")
    return commit, set(expected.values()), collections.Counter(s.status for s in scans if s.status != "PROCESSING" or s.finished_at is None) + collections.Counter({"COMPLETED":len(complete)})


def describe(client, url, args, *, expected, ambiguous, repeats, plans):
    response = client.get(url, args)
    assert response.status_code == 200, response.status_code
    first = []
    with connection.execute_wrapper(trace(first)):
        response = client.get(url, args)
    assert response.status_code == 200
    if os.environ["QUAL_VARIANT"] != "A":
        selection = response.context_data["selection"] if hasattr(response, "context_data") else response.context["selection"]
        assert {str(item) for item in selection["completed_ids"]} == expected
        assert selection["ambiguous"] is ambiguous
        assert selection["finding_count"] == sum(scan["finding_count"] for scan in selection["scans"])
    samples = []
    cpu_start = time.process_time()
    pg_start = cpu_usec()
    for _ in range(repeats):
        n = []
        def count(execute, sql, params, many, context):
            n.append(None)
            return execute(sql, params, many, context)
        start = time.perf_counter()
        with connection.execute_wrapper(count):
            result = client.get(url, args)
        assert result.status_code == 200
        samples.append({"ms": (time.perf_counter()-start)*1000, "queries":len(n)})
    pg_cpu = cpu_usec() - pg_start
    app_cpu = time.process_time() - cpu_start
    if plans:
        for row in first:
            if row["sql"].lstrip().upper().startswith("SELECT"):
                with connection.cursor() as cursor:
                    cursor.execute("EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON) "+row["sql"], row["params"])
                    row["plan"] = cursor.fetchone()[0]
    times = sorted(row["ms"] for row in samples)
    return {"p50_ms":statistics.median(times), "p95_ms":times[math.ceil(len(times)*.95)-1],
            "queries": sorted({row["queries"] for row in samples}), "app_cpu_s":app_cpu,
            "pg_cgroup_cpu_s":pg_cpu/1_000_000, "process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "body_bytes":len(response.content), "correct":True, "samples":samples, "trace":first}


def main():
    if sys.flags.optimize or connection.settings_dict["NAME"] not in {"aspm_zero_ab_a", "aspm_zero_ab_b", "zf_overview"}:
        raise SystemExit("Requires an explicitly owned diagnostic database and enabled assertions.")
    from django.test.utils import setup_test_environment  # noqa: PLC0415
    setup_test_environment()
    with transaction.atomic():
        variant = os.environ["QUAL_VARIANT"]
        pt = Product_Type.objects.create(name="Qualification SQL")
        product = Product.objects.create(name="Qualification SQL", prod_type=pt, description="Synthetic")
        reader = get_user_model().objects.create_user(username="zfq-synthetic-reader")
        product.authorized_users.add(reader.pk)
        repo = Repository.objects.create(product=product, url="https://example.invalid/zfq")
        client = Client()
        client.force_login(reader)
        cases = []
        base, _, _ = seed(repo, reader, "base", 10, "reruns")
        for count in (1, 10, 100, 1000):
            for mode in ("reruns", "mixed"):
                label = f"{mode}-{count}"
                commit, expected, statuses = seed(repo, reader, label, count, mode)
                url = reverse("aspm_commit_evidence", args=[commit.pk])
                args = {"tab":"overview"}
                if mode == "mixed" and count > 1 and variant != "A":
                    args["pipeline"] = "pipeline:pipeline-0"
                cases.append({"case":label,"scan_runs":count,"status_counts":statuses,
                    **describe(client,url,args,expected=expected,ambiguous=False,repeats=30,plans=True)})
                if mode == "mixed" and count > 1 and variant != "A":
                    cases.append({"case":label+"-ambiguous","scan_runs":count,
                      **describe(client,url,{"tab":"overview"},expected=set(),ambiguous=True,repeats=30,plans=True)})
                if count == 1000 and mode == "reruns" and variant != "A":
                    for tab in ("originals","findings","changes"):
                        query = {"tab":tab}
                        if tab == "changes":
                            query.update(base=base.pk,category="fixed")
                        cases.append({"case":label+"-"+tab,"scan_runs":count,**describe(
                            client,url,query,expected=expected,ambiguous=False,repeats=20,plans=True)})
        if variant != "A":
            commit, expected, _ = seed(repo, reader, "large", 1, "large", observations=10000)
            for tab in ("overview","findings"):
                cases.append({"case":"10000-observations-"+tab,"scan_runs":1,"observations":10000,
                   **describe(client,reverse("aspm_commit_evidence",args=[commit.pk]),{"tab":tab},
                              expected=expected,ambiguous=False,repeats=30,plans=True)})
        transaction.set_rollback(True)
    print(json.dumps({"variant":variant,"cases":cases,"fixture_rolled_back":True},default=str))


main()
