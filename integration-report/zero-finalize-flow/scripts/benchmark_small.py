"""Small fresh A/B diagnostic; does not replace frozen 1M Core9/acceptance qualification."""
# ruff: noqa: INP001, T201
import json
import os
import resource
import statistics
import time
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from dojo.aspm_ingestion.models import ScanRun
from dojo.aspm_ingestion.services import finalize_commit, issue_token, request_report
from dojo.aspm_ingestion.storage import private_path
from dojo.aspm_ingestion.tasks import process_job
from dojo.models import Product, Product_Type


def measure(function):
    start = time.perf_counter()
    with CaptureQueriesContext(connection) as queries:
        result = function()
    return result, {"seconds": time.perf_counter() - start, "sql_queries": len(queries)}


def summary(rows):
    times = sorted(row["seconds"] for row in rows)
    return {"n": len(rows), "median_ms": statistics.median(times) * 1000,
            "p95_ms": times[max(0, int(len(times) * .95) - 1)] * 1000,
            "queries": sorted(set(row["sql_queries"] for row in rows))}


def main():
    variant = os.environ["ZERO_VARIANT"]
    assert variant in {"A", "B"}
    assert settings.DATABASES["default"]["NAME"] == "aspm_zero_ab_" + variant.lower()
    cpu_start = time.process_time()
    product_type, = Product_Type.objects.bulk_create([Product_Type(name="Small A/B")])
    product, = Product.objects.bulk_create([Product(name="Small A/B", description="Fresh identical diagnostic", prod_type=product_type)])
    user = get_user_model().objects.create_user(username="small-ci", password=None)
    _, raw = issue_token(user=user, product=product, scopes=["submit", "status", "read", "reports"],
                         expires_at=timezone.now() + timedelta(hours=1), label="Small A/B")
    browser_user = get_user_model().objects.create_user(username="small-reader", password=None)
    product.authorized_users.add(browser_user.pk)
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION="ASPM " + raw)
    browser = Client()
    browser.force_login(browser_user)
    accepted, completion, snapshots, reports = [], [], [], []
    samples = 6
    size = 100
    artifact = json.dumps({"findings": [{"title": f"Diagnostic finding {i}", "severity": "High", "description": "Small synthetic A/B", "cwe": 79} for i in range(size)]}).encode()
    with patch("dojo.aspm_ingestion.services.wake_dispatcher"):
        for i in range(samples):
            response, timing = measure(lambda: api.post(reverse("aspm_v1:scans"), {
                "project_id": product.pk, "repository_url": "https://example.invalid/small-ab", "commit_sha": "a" * 40,
                "scanner_type": "Generic Findings Import", "pipeline_id": "small-ab", "job_id": "generic",
                "scan_scope": "repository-v1", "attempt_number": i + 1, "idempotency_key": f"small/{i}",
                "file": SimpleUploadedFile("scan.json", artifact),
            }, format="multipart"))
            assert response.status_code == 202, response.content
            accepted.append(timing)
            scan = ScanRun.objects.get(pk=response.json()["id"])
            _, timing = measure(lambda: process_job("scan", str(scan.pk)))
            completion.append(timing)
            scan.refresh_from_db()
            assert scan.status == "COMPLETED" and scan.finding_count == size
            snapshots.append(scan.timings["observation_seconds"])
        for i in range(3):
            def freeze():
                if variant == "A":
                    frozen = finalize_commit(scan.commit, [scan.scanner], scan_ids=[scan.pk])
                    return request_report(scan.commit, frozen.pk)
                return request_report(scan.commit, scan_ids=[scan.pk], expected_scanners=[scan.scanner])
            report, timing = measure(freeze)
            _, generation = measure(lambda: process_job("report", str(report.pk)))
            report.refresh_from_db()
            assert report.status == "COMPLETED"
            reports.append({"fixation": timing, "generation": generation,
                            "bytes": {kind: private_path(getattr(report, kind + "_path")).stat().st_size for kind in ("html", "json")}})
        views = {}
        for tab in ("overview", "findings", "reports"):
            observations = []
            for _ in range(21):
                response, timing = measure(lambda: browser.get(reverse("aspm_commit_evidence", args=[scan.commit_id]), {"tab": tab}))
                assert response.status_code == 200
                observations.append(timing)
            views[tab] = summary(observations[1:])
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_total_relation_size('dojo_findingobservation'), pg_database_size(current_database())")
        storage = cursor.fetchone()
    print(json.dumps({"variant": variant, "diagnostic_only": True,
                      "method": "Django in-process client, real PostgreSQL/importer; no broker queue or network latency", "scans": samples,
                      "findings_per_scan": size, "acceptance": summary(accepted), "completion": summary(completion),
                      "snapshot_seconds": snapshots, "views": views, "reports": reports,
                      "observation_relation_bytes": storage[0], "database_bytes": storage[1],
                      "app_cpu_seconds": time.process_time() - cpu_start,
                      "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))


main()
