"""Run via manage.py shell on an isolated disposable database; never on production."""
# ruff: noqa: INP001, T201, PLC0415
import hashlib
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections, connections
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from dojo.aspm_ingestion.models import CommitScanSetMembership, GeneratedReport, IngestionJob, ScanRun
from dojo.aspm_ingestion.services import issue_token
from dojo.aspm_ingestion.storage import private_path
from dojo.aspm_ingestion.tasks import dispatch_jobs, process_job
from dojo.models import Product, Product_Type


def main():
    if settings.DATABASES["default"]["NAME"] != "aspm_zero":
        raise RuntimeError("This harness is restricted to the owned aspm_zero database")
    run = uuid.uuid4().hex[:12]
    user_model = get_user_model()
    product_type, = Product_Type.objects.bulk_create([Product_Type(name="Zero " + run)])
    product, = Product.objects.bulk_create([Product(name="Zero " + run, description="Owned qualification", prod_type=product_type)])
    service = user_model.objects.create_user(username="zero-ci-" + run, password=None)
    _, raw = issue_token(user=service, product=product, scopes=["submit", "read", "status", "reports"],
                         expires_at=timezone.now() + timedelta(hours=4), label="zero qualification")
    reader = user_model.objects.create_user(username="zero-reader-" + run, password="ZeroFinalize-local-smoke-2026")
    product.authorized_users.add(reader.pk)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="ASPM " + raw)
    checks = {}
    source = json.dumps({"findings": [{"title": "Race historical finding", "severity": "High", "description": "Fixture", "cwe": 79}]}).encode()

    def upload(key, scanner="Generic Findings Import", body=source):
        return client.post(reverse("aspm_v1:scans"), {
            "project_id": product.pk, "repository_url": "https://example.invalid/zero/" + run,
            "commit_sha": "a" * 40, "scanner_type": scanner, "idempotency_key": key,
            "pipeline_id": run, "scan_scope": "repository-v1", "job_id": scanner,
            "file": SimpleUploadedFile("report.json", body),
        }, format="multipart")

    def parallel(functions):
        barrier = Barrier(len(functions))

        def wrapped(function):
            close_old_connections()
            try:
                barrier.wait(timeout=15)
                return function()
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=len(functions)) as pool:
            return list(pool.map(wrapped, functions))

    with patch("dojo.aspm_ingestion.services.wake_dispatcher"):
        scans = parallel([lambda: upload("generic"), lambda: upload("trivy", "Trivy Scan", b'{"SchemaVersion":2,"Results":[]}')])
        assert [row.status_code for row in scans] == [202, 202]
        commit_id = scans[0].json()["commit"]
        assert commit_id == scans[1].json()["commit"]
        checks["parallel_scanners"] = True
        ids = [row.json()["id"] for row in scans]
        parallel([lambda identifier=identifier: process_job("scan", identifier) for identifier in ids])
        assert ScanRun.objects.filter(pk__in=ids, status="COMPLETED").count() == 2
        checks["parallel_imports"] = True
        repeated = parallel([lambda: upload("same-job") for _ in range(4)])
        assert sorted(row.status_code for row in repeated) == [200, 200, 200, 202]
        assert len({row.json()["id"] for row in repeated}) == 1
        checks["idempotent_delivery"] = True
        assert upload("same-job", body=b'{"findings":[]}').status_code == 409
        checks["idempotency_conflict"] = True
        pending_id = repeated[0].json()["id"]
        parallel([lambda: process_job("scan", pending_id), lambda: process_job("scan", pending_id)])
        assert ScanRun.objects.get(pk=pending_id).attempt == 1
        checks["duplicate_worker_delivery"] = True
        reports_url = reverse("aspm_v1:reports", args=[commit_id])
        reports = parallel([lambda: client.post(reports_url, {}, format="json") for _ in range(2)])
        assert sorted(row.status_code for row in reports) == [202, 202]
        assert sorted(row.json()["version"] for row in reports) == [1, 2]
        checks["parallel_report_versions"] = True
        racing = parallel([lambda: upload("late"), lambda: client.post(reports_url, {}, format="json")])
        assert [row.status_code for row in racing] == [202, 202]
        late_id = racing[0].json()["id"]
        report = GeneratedReport.objects.get(pk=racing[1].json()["id"])
        frozen = json.dumps(report.manifest, sort_keys=True)
        assert late_id not in report.scan_set.scan_ids
        process_job("scan", late_id)
        process_job("report", str(report.pk))
        report.refresh_from_db()
        assert report.status == "COMPLETED"
        assert json.dumps(report.manifest, sort_keys=True) == frozen
        membership = {str(pk) for pk in CommitScanSetMembership.objects.filter(scan_set=report.scan_set).values_list("scan_id", flat=True)}
        payload = json.loads(private_path(report.json_path).read_text())
        assert membership == set(report.scan_set.scan_ids) == {row["id"] for row in payload["report"]["scans"]}
        assert {row["scan_id"] for row in payload["observations"]} <= membership
        assert late_id not in membership
        checks["upload_during_export_and_manifest_integrity"] = True
        old_bytes = {kind: hashlib.sha256(private_path(getattr(report, kind + "_path")).read_bytes()).hexdigest() for kind in ("html", "json")}
        process_job("report", str(report.pk))
        assert old_bytes == report.checksums
        checks["old_report_immutable"] = True
        failed = upload("failed", body=b"invalid").json()["id"]
        process_job("scan", failed)
        assert client.get(reverse("aspm_v1:scan-detail", args=[failed])).json()["status"] == "FAILED"
        assert failed in {row["id"] for row in client.get(reverse("aspm_v1:commit-scans", args=[commit_id])).json()}
        checks["failed_history"] = True
        queued = upload("broker-fault").json()["id"]
        with patch("dojo.aspm_ingestion.tasks.process_job.apply_async", side_effect=ConnectionError):
            dispatch_jobs()
        assert IngestionJob.objects.filter(scan_id=queued).exists()
        IngestionJob.objects.filter(scan_id=queued).update(next_dispatch_at=timezone.now())
        with patch("dojo.aspm_ingestion.tasks.process_job.apply_async") as send:
            dispatch_jobs()
        assert send.called
        process_job("scan", queued)
        assert ScanRun.objects.get(pk=queued).status == "COMPLETED"
        checks["outbox_fault_and_recovery"] = True
    from django.contrib.sessions.backends.db import SessionStore
    from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
    session = SessionStore()
    session[SESSION_KEY] = str(reader.pk)
    session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    session[HASH_SESSION_KEY] = reader.get_session_auth_hash()
    session.save()
    runtime = Path("/zero-runtime")
    runtime.mkdir(exist_ok=True)
    credential_path = runtime / "credentials.json"
    credential_path.write_text(json.dumps({"token": raw, "product_id": product.pk, "commit_id": commit_id,
                                           "repository_id": ScanRun.objects.get(pk=ids[0]).commit.repository_id,
                                           "session": session.session_key, "report_id": str(report.pk), "run": run}))
    credential_path.chmod(0o600)
    print(json.dumps({"run": run, "checks": checks, "passed": all(checks.values()), "commit_id": commit_id}))


main()
