"""Bounded, isolated measurement of the added historical model; never a production load generator."""

import json
import time
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone

from dojo.aspm_ingestion.models import IngestionJob, ScanRun
from dojo.aspm_ingestion.services import accept_scan, finalize_commit, issue_token, request_report
from dojo.aspm_ingestion.storage import private_path, safe_name, save_original
from dojo.aspm_ingestion.tasks import MeasuredReImporter, generate_report, prepare_test, snapshot_findings
from dojo.models import Finding, Product, Product_Type, Test


class Command(BaseCommand):
    help = "Measure snapshot/report/WAL cost for at most 1M synthetic Findings in an isolated benchmark database."

    def add_arguments(self, parser):
        parser.add_argument("--rows", type=int, default=10000)
        parser.add_argument("--confirm-isolated-database", required=True)
        parser.add_argument("--reuse-fixture-test", type=int, help="Reuse an unattached synthetic Test; the command never deletes evidence.")

    def handle(self, *args, **options):
        database = connection.settings_dict["NAME"]
        if database != options["confirm_isolated_database"] or not database.startswith("aspm_history_benchmark"):
            msg = "Use a dedicated database named aspm_history_benchmark*. Never point this command at a baseline or production database."
            raise CommandError(msg)
        rows = options["rows"]
        if options["reuse_fixture_test"]:
            self.measure_existing_fixture(options["reuse_fixture_test"], rows)
            return
        if not 1 <= rows <= 1000000 or Finding.objects.exists():
            msg = "Use an empty dedicated database and --rows between 1 and 1000000."
            raise CommandError(msg)
        suffix = uuid.uuid4().hex[:12]
        product_type = Product_Type.objects.create(name=f"ASPM history benchmark {suffix}")
        product = Product.objects.create(name=f"ASPM history benchmark {suffix}", description="Synthetic fixture", prod_type=product_type)
        user = get_user_model().objects.create_user(username=f"history-benchmark-{suffix}", password=None)
        token, _ = issue_token(user=user, product=product, scopes=["submit"], expires_at=timezone.now() + timedelta(days=1), label="isolated benchmark")
        scan, _ = accept_scan(token, {"project_id": product.pk, "repository_url": "https://example.com/aspm/benchmark", "commit_sha": "b" * 40,
                                     "scanner_type": "Generic Findings Import", "idempotency_key": suffix},
                              SimpleUploadedFile("synthetic.json", json.dumps({"findings": [{"title": "Synthetic observation benchmark", "description": "Synthetic representative observation; no production data", "severity": "High", "cwe": 79}]}).encode()))
        scan.attempt = 1
        scan.started_at = timezone.now()
        ScanRun.objects.filter(pk=scan.pk).update(status="PROCESSING", attempt=1, started_at=scan.started_at)
        test = prepare_test(scan)
        importer = MeasuredReImporter(test=test, scan_type=scan.scanner, user=user, scan_date=timezone.now(), deduplication_execution_mode="sync", push_to_jira=False)
        importer.phase_timings = {}
        with private_path(scan.artifact_path).open("rb") as report_file:
            importer.process_scan(report_file)
        finding = Finding.objects.get(test=test)
        start = time.monotonic()
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_current_wal_lsn()")
            seed_lsn = cursor.fetchone()[0]
            fields = [field for field in Finding._meta.local_concrete_fields if not field.primary_key]
            quote = connection.ops.quote_name
            columns = ",".join(quote(field.column) for field in fields)
            expressions = []
            for field in fields:
                if field.name == "title":
                    expressions.append("'ASPM synthetic history fixture ' || g.i")
                elif field.name == "hash_code":
                    expressions.append("md5('aspm-synthetic-history-' || g.i::text)")
                else:
                    expressions.append("f." + quote(field.column))
            # Identifiers come exclusively from Django model metadata; values are bound parameters.
            # Bounded transactions keep deferred FK validation and trigger event queues bounded too.
            for first in range(1, rows, 10000):
                cursor.execute(f"INSERT INTO {quote(Finding._meta.db_table)} ({columns}) SELECT {','.join(expressions)} FROM {quote(Finding._meta.db_table)} f CROSS JOIN generate_series(%s, %s) g(i) WHERE f.id=%s", [first, min(rows - 1, first + 9999), finding.pk])
            cursor.execute("SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), %s)::bigint", [seed_lsn])
            seed_wal = cursor.fetchone()[0]
            cursor.execute("SELECT pg_current_wal_lsn()")
            observation_lsn = cursor.fetchone()[0]
        seed_seconds = time.monotonic() - start
        self.measure(scan, rows, observation_lsn, seed_seconds=seed_seconds, seed_wal=seed_wal)

    def measure_existing_fixture(self, test_id, rows):
        if not 1 <= rows <= 1000000 or Finding.objects.count() != rows or ScanRun.objects.exists():
            msg = "Reuse requires an unattached synthetic fixture, empty evidence tables and at most 1M Findings."
            raise CommandError(msg)
        test = Test.objects.select_related("engagement__commit__repository", "lead").get(pk=test_id)
        if test.finding_set.count() != rows or not test.engagement.commit_id:
            msg = "The selected Test does not contain the complete synthetic fixture."
            raise CommandError(msg)
        upload = SimpleUploadedFile("synthetic.json", b'{"fixture":"synthetic SQL-cloned Findings; not a parser throughput measurement"}')
        key, digest, size, storage_seconds = save_original(upload)
        user = get_user_model().objects.filter(username__startswith="history-benchmark-").first()
        scan = ScanRun.objects.create(product_id=test.engagement.product_id, commit_id=test.engagement.commit_id, test=test,
                                      submitted_by=user, delivery_key=uuid.uuid4().hex, fingerprint=digest, scanner=test.scan_type,
                                      artifact_path=key, artifact_sha256=digest, artifact_size=size, original_name=safe_name(upload.name),
                                      status="PROCESSING", attempt=1, started_at=timezone.now(), timings={"artifact_storage_seconds": storage_seconds})
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_current_wal_lsn()")
            observation_lsn = cursor.fetchone()[0]
        self.measure(scan, rows, observation_lsn, seed_seconds=0, seed_wal=0)

    def measure(self, scan, rows, observation_lsn, *, seed_seconds, seed_wal):
        count, severity, snapshot_seconds = snapshot_findings(scan)
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), %s)::bigint", [observation_lsn])
            snapshot_wal = cursor.fetchone()[0]
        ScanRun.objects.filter(pk=scan.pk).update(status="COMPLETED", observation_generation=1, finding_count=count, severity_summary=severity, finished_at=timezone.now())
        IngestionJob.objects.filter(scan=scan).delete()
        scan_set = finalize_commit(scan.commit, [scan.scanner])
        report = request_report(scan.commit, scan_set.pk)
        generate_report(report)
        report.refresh_from_db()
        with connection.cursor() as cursor:
            sizes = {}
            for table in ("dojo_finding", "dojo_findingobservation"):
                cursor.execute("SELECT pg_table_size(%s), pg_indexes_size(%s), pg_total_relation_size(%s)", [table, table, table])
                sizes[table] = dict(zip(("table_bytes", "index_bytes", "total_bytes"), cursor.fetchone(), strict=True))
        result = {"database": connection.settings_dict["NAME"], "rows": rows, "actual_finding_count": Finding.objects.count(), "actual_observation_count": count,
                  "fixture": "Synthetic Finding rows cloned using SQL, excluding parser/dedup scaling claims; snapshot and report use production code.",
                  "seed_seconds": seed_seconds, "seed_wal_bytes": seed_wal, "snapshot_seconds": snapshot_seconds, "snapshot_wal_bytes": snapshot_wal,
                  "generation_seconds": report.timings["generation_seconds"], "sizes": sizes,
                  "json_bytes": private_path(report.json_path).stat().st_size, "html_bytes": private_path(report.html_path).stat().st_size,
                  "scan_id": str(scan.pk), "report_id": str(report.pk), "report_checksums": report.checksums}
        self.stdout.write(json.dumps(result, indent=2))
