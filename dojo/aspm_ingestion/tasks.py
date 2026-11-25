import hashlib
import html
import json
import logging
import os
import pathlib
import time
import uuid
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta

from crum import impersonate
from django.core.files import File
from django.db import connection, transaction
from django.db.models import F
from django.utils import timezone

from dojo.aspm_ingestion.logging import private_import_logs
from dojo.aspm_ingestion.models import FindingObservation, GeneratedReport, IngestionJob, ScanRun
from dojo.aspm_ingestion.storage import bounded_text_output, private_path, sync_directories, verify_original
from dojo.celery import app
from dojo.importers.default_importer import DefaultImporter
from dojo.importers.default_reimporter import DefaultReImporter
from dojo.importers.import_lock import lock_tests_under_import, unlock_tests_under_import
from dojo.models import Development_Environment, Engagement, Finding
from dojo.vulnerability.models import FindingVulnerabilityReference

logger = logging.getLogger(__name__)


@contextmanager
def job_lock(identifier):
    """Session fencing survives per-finding transactions; worker death releases it automatically."""
    key = int.from_bytes(hashlib.sha256(str(identifier).encode()).digest()[:8], "big", signed=True)
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [key])
        acquired = cursor.fetchone()[0]
    try:
        yield acquired
    finally:
        if acquired:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [key])


@app.task(name="dojo.aspm_ingestion.dispatch_jobs", ignore_result=True)
def dispatch_jobs(**kwargs):
    """A broker ACK never deletes the outbox. Re-deliver until a terminal DB state is durable."""
    with transaction.atomic():
        jobs = list(IngestionJob.objects.select_for_update(skip_locked=True).filter(next_dispatch_at__lte=timezone.now()).order_by("next_dispatch_at")[:100])
        for job in jobs:
            job.next_dispatch_at = timezone.now() + timedelta(seconds=60)
            job.deliveries = F("deliveries") + 1
            job.save(update_fields=["next_dispatch_at", "deliveries"])
    for job in jobs:
        try:
            process_job.apply_async(args=["scan" if job.scan_id else "report", str(job.scan_id or job.report_id)], kwargs={"dispatched_at": timezone.now().isoformat()})
        except Exception:
            # The next periodic dispatch retries, including process death before this send.
            logger.warning("ASPM broker dispatch deferred for job %s", job.pk)

    from dojo.webhooks.tasks import dispatch_webhooks  # noqa: PLC0415 -- shared outbox dispatcher

    dispatch_webhooks()


class MeasuredReImporter(DefaultReImporter):

    """Instrumentation around the existing pipeline, with no replacement parsing logic."""

    def parse_findings(self, *args, **kwargs):
        start = time.monotonic()
        result = super().parse_findings(*args, **kwargs)
        self.phase_timings["parser_seconds"] = time.monotonic() - start
        return result

    def process_findings(self, *args, **kwargs):
        start = time.monotonic()
        result = super().process_findings(*args, **kwargs)
        self.phase_timings["reimport_dedup_seconds"] = time.monotonic() - start
        return result


def prepare_test(scan):
    if scan.test_id:
        return scan.test
    # Only metadata creation is transactional. No parsing or file I/O under row locks.
    with transaction.atomic():
        today = timezone.localdate()
        engagement = scan.engagement or Engagement.objects.create(
            product_id=scan.product_id, commit=scan.commit,
            name=f"ASPM {scan.commit.sha[:12]} / {scan.pk}", engagement_type="CI/CD",
            target_start=today, target_end=today + timedelta(days=365), status="In Progress",
            commit_hash=scan.commit.sha, source_code_management_uri=scan.commit.repository.url,
        )
        # The shared environment has no unique name constraint. Serialize only metadata
        # creation, and tolerate pre-existing duplicate names without rewriting history.
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ["aspm.ingestion.development-environment"])
        environment = Development_Environment.objects.filter(name="Development").order_by("pk").first()
        if environment is None:
            environment = Development_Environment.objects.create(name="Development")
        importer = DefaultImporter(engagement=engagement, scan_type=scan.scanner, user=scan.submitted_by,
                                   environment=environment, test_title=f"ASPM {scan.pk}", scan_date=timezone.now(),
                                   commit_hash=scan.commit.sha, deduplication_execution_mode="sync", push_to_jira=False)
        test = importer.create_test(scan.scanner)
        ScanRun.objects.filter(pk=scan.pk).update(test=test)
        scan.test = test
    return test


SNAPSHOT_FIELDS = ("id", "title", "description", "severity", "cwe", "cve", "file_path", "line", "component_name", "component_version", "hash_code", "unique_id_from_tool", "service", "active", "verified", "false_p", "duplicate", "out_of_scope", "is_mitigated", "mitigation", "date")


def snapshot_findings(scan):
    start = time.monotonic()
    severity = Counter()
    count = 0
    # Failed generations are never visible. A retry publishes a fresh generation atomically.
    rows = Finding.objects.filter(test_id=scan.test_id).order_by("pk").values(*SNAPSHOT_FIELDS).iterator(chunk_size=500)
    batch = []

    def flush(values):
        vulnerabilities = {}
        for finding_id, value in FindingVulnerabilityReference.objects.filter(finding_id__in=[row["id"] for row in values]).order_by("finding_id", "order").values_list("finding_id", "vulnerability__vulnerability_id"):
            vulnerabilities.setdefault(finding_id, []).append(value)
        observations = []
        for row in values:
            row["date"] = row["date"].isoformat() if row["date"] else None
            primary = row.pop("cve")
            row["vulnerability_ids"] = list(dict.fromkeys(([primary] if primary else []) + vulnerabilities.get(row["id"], [])))
            identity = hashlib.sha256(json.dumps([scan.scanner, row["service"], row["hash_code"] or row["unique_id_from_tool"] or row["title"]], ensure_ascii=True).encode()).hexdigest()
            observations.append(FindingObservation(scan=scan, generation=scan.attempt, source_finding_id=row["id"], identity=identity, severity=row["severity"], snapshot=row))
        FindingObservation.objects.bulk_create(observations, batch_size=500)

    for row in rows:
        severity[row["severity"]] += 1
        count += 1
        batch.append(row)
        if len(batch) == 500:
            flush(batch)
            batch = []
    if batch:
        flush(batch)
    return count, dict(severity), time.monotonic() - start


def import_scan(scan):
    verify_original(scan)
    test = prepare_test(scan)
    timings = dict(scan.timings)
    timings["acceptance_to_start_seconds"] = max(0, (scan.started_at - scan.created_at).total_seconds())
    with impersonate(scan.submitted_by), private_import_logs():
        importer = MeasuredReImporter(
            test=test, scan_type=scan.scanner, user=scan.submitted_by, scan_date=timezone.now(),
            environment=test.environment, commit_hash=scan.commit.sha,
            branch_tag=scan.metadata.get("branch", ""), build_id=scan.metadata.get("build_id", ""),
            deduplication_execution_mode="sync", close_old_findings=False, push_to_jira=False,
        )
        importer.phase_timings = {}
        locked = lock_tests_under_import([test.pk])
        try:
            with private_path(scan.artifact_path).open("rb") as source:
                importer.process_scan(File(source, name=scan.original_name))
            if not getattr(importer, "deduplication_complete", False):
                msg = "deduplication_incomplete"
                raise RuntimeError(msg)
            timings.update(importer.phase_timings)
            count, severity, seconds = snapshot_findings(scan)
        finally:
            unlock_tests_under_import(locked)
    timings["observation_seconds"] = seconds
    with transaction.atomic():
        ScanRun.objects.filter(pk=scan.pk).update(
            status=ScanRun.Status.COMPLETED, finished_at=timezone.now(), error_code="",
            observation_generation=scan.attempt, finding_count=count, severity_summary=severity, timings=timings,
        )
        IngestionJob.objects.filter(scan=scan).delete()


def report_observations(report):
    for scan in report.manifest["scans"]:
        if scan["status"] != ScanRun.Status.COMPLETED:
            continue
        for snapshot in FindingObservation.objects.filter(scan_id=scan["id"], generation=scan["observation_generation"]).order_by("pk").values_list("snapshot", flat=True).iterator(chunk_size=500):
            yield {"scan_id": scan["id"], "scanner": scan["scanner"], **snapshot}


def generate_report(report):
    start = time.monotonic()
    prefix = f"reports/{report.pk}/{uuid.uuid4().hex}"
    json_key, html_key = f"{prefix}/report.json", f"{prefix}/report.html"
    json_path, html_path = private_path(json_key), private_path(html_key)
    json_path.parent.mkdir(mode=0o700, parents=True)
    severity = Counter()
    for scan in report.manifest["scans"]:
        if scan["status"] == ScanRun.Status.COMPLETED:
            severity.update(scan["severity_summary"])
    manifest = {**report.manifest, "severity_summary": dict(severity)}
    try:
        with bounded_text_output(json_path) as json_output, bounded_text_output(html_path) as html_output:
            pathlib.Path(json_path).chmod(0o600)
            pathlib.Path(html_path).chmod(0o600)
            # Stream observations. Memory stays bounded even for million-row reports.
            json_output.write('{"report":' + json.dumps(manifest, ensure_ascii=True) + ',"observations":[')
            html_output.write('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; style-src &#39;unsafe-inline&#39;"><title>ASPM commit report</title><style>body{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:2em auto;padding:0 1em;color:#202124}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f4f4;padding:1em}article{border-bottom:1px solid #ddd;padding:1em 0}h1,h2,h3{line-height:1.25}a{overflow-wrap:anywhere}</style></head><body><h1>ASPM generated commit report</h1>')
            html_output.write("<p>Coverage: " + html.escape(manifest.get("selection", {}).get("coverage") or ("complete" if manifest["complete"] else "INCOMPLETE")) + "</p><pre>" + html.escape(json.dumps(manifest, indent=2)) + "</pre><h2>Original scanner artifacts</h2><ul>")
            for scan in manifest["scans"]:
                html_output.write('<li><a href="' + html.escape(scan["original_url"], quote=True) + '">' + html.escape(scan["scanner"]) + "</a></li>")
            html_output.write("</ul><h2>Historical finding observations</h2>")
            first = True
            for observation in report_observations(report):
                serialized = json.dumps(observation, ensure_ascii=True)
                json_output.write(("" if first else ",") + serialized)
                html_output.write("<article><h3>" + html.escape(observation["title"]) + "</h3><p>" + html.escape(observation["scanner"] + " · " + observation["severity"]) + "</p><pre>" + html.escape(serialized) + "</pre></article>")
                first = False
            json_output.write("]}")
            html_output.write("</body></html>")
            for output in (json_output, html_output):
                output.flush()
                os.fsync(output.fileno())
        checksums = {}
        sync_directories(json_path)
        for kind, path in (("json", json_path), ("html", html_path)):
            digest = hashlib.sha256()
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
            checksums[kind] = digest.hexdigest()
        with transaction.atomic():
            GeneratedReport.objects.filter(pk=report.pk).update(status=ScanRun.Status.COMPLETED, json_path=json_key, html_path=html_key, checksums=checksums, timings={"generation_seconds": time.monotonic() - start})
            IngestionJob.objects.filter(report=report).delete()
    except BaseException:
        json_path.unlink(missing_ok=True)
        html_path.unlink(missing_ok=True)
        raise


@app.task(name="dojo.aspm_ingestion.process_job", acks_late=True, reject_on_worker_lost=True, soft_time_limit=840, time_limit=900, ignore_result=True)
def process_job(kind, identifier, *, dispatched_at=None, **kwargs):
    with job_lock(identifier) as acquired:
        if not acquired:
            return
        if kind == "scan":
            scan = ScanRun.objects.select_related("commit__repository", "engagement", "submitted_by", "test__environment").get(pk=identifier)
            if scan.status in {ScanRun.Status.COMPLETED, ScanRun.Status.FAILED}:
                return
            recovered = scan.status == ScanRun.Status.PROCESSING
            if recovered:
                scan.recovery_count += 1
            if scan.recovery_count >= 3:
                with transaction.atomic():
                    ScanRun.objects.filter(pk=scan.pk).update(status=ScanRun.Status.FAILED, error_code="worker_recovery_limit", finished_at=timezone.now())
                    IngestionJob.objects.filter(scan=scan).delete()
                return
            scan.attempt += 1
            scan.started_at = timezone.now()
            scan.timings.pop("queue_wait_seconds", None)
            if dispatched_at and not recovered:
                try:
                    published_at = datetime.fromisoformat(dispatched_at)
                    scan.timings["queue_wait_seconds"] = max(0, (scan.started_at - published_at).total_seconds())
                except (ValueError, TypeError):
                    # Redelivered or externally supplied tasks may have no usable publish timestamp.
                    pass
            ScanRun.objects.filter(pk=scan.pk).update(status=ScanRun.Status.PROCESSING, attempt=scan.attempt, recovery_count=scan.recovery_count, started_at=scan.started_at)
            try:
                import_scan(scan)
            except Exception:
                # Parser errors may contain report text/secrets. Persist only a stable safe code.
                with transaction.atomic():
                    ScanRun.objects.filter(pk=scan.pk).update(status=ScanRun.Status.FAILED, error_code="import_failed", finished_at=timezone.now())
                    IngestionJob.objects.filter(scan=scan).delete()
        elif kind == "report":
            report = GeneratedReport.objects.get(pk=identifier)
            if report.status in {ScanRun.Status.COMPLETED, ScanRun.Status.FAILED}:
                return
            try:
                generate_report(report)
            except Exception:
                with transaction.atomic():
                    GeneratedReport.objects.filter(pk=report.pk).update(status=ScanRun.Status.FAILED, error_code="generation_failed")
                    IngestionJob.objects.filter(report=report).delete()
