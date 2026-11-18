"""
Strict PostgreSQL race oracles; intentionally red on an unsafe candidate.

Run with run-unittest.sh and the isolated configuration produced by phase1_lab.py.
Hooks only pause real application code; persistence and serializers remain real.
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from celery.contrib.testing.worker import start_worker
from crum import impersonate
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections, connection, connections
from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework.test import APIClient

from dojo.celery import app
from dojo.finding.api.views import FindingViewSet
from dojo.finding.deduplication import do_dedupe_finding_task
from dojo.importers.default_importer import DefaultImporter
from dojo.importers.default_reimporter import DefaultReImporter
from dojo.models import (
    Development_Environment,
    Dojo_User,
    Finding,
    System_Settings,
    Test,
)
from unittests.test_dedupe_delete_commit_race import _CommittedFindingsMixin

EVIDENCE = Path("/tmp/rc5-evidence")
EVIDENCE.mkdir(exist_ok=True)


class PatchRaces(_CommittedFindingsMixin, SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.product.authorized_users.add(self.user.pk)
        self.finding = self._create_findings("RC5 race " + self.suffix)[0]
        Finding.objects.filter(pk=self.finding.pk).update(
            description="Original description",
            mitigation="Original mitigation",
        )
        self.url = reverse("finding-detail", args=[self.finding.pk])

    def request(self, changes, method="patch", user_id=None):
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(user=Dojo_User.objects.get(pk=user_id or self.user.pk))
            response = getattr(client, method)(self.url, changes, format="json")
            return response.status_code, response.data
        finally:
            connections.close_all()

    def record(self, data):
        (EVIDENCE / (self._testMethodName + ".json")).write_text(
            json.dumps(data, indent=2, default=str) + "\n",
        )

    def concurrent(self, changes):
        barrier = threading.Barrier(len(changes))
        real_get = FindingViewSet.get_object
        real_update = FindingViewSet.perform_update
        completed = []
        mutex = threading.Lock()

        def first_read(view):
            obj = real_get(view)
            if not getattr(view, "_race_first_read", False):
                view._race_first_read = True
                barrier.wait(timeout=45)
            return obj

        def update(view, serializer):
            real_update(view, serializer)
            with mutex:
                completed.append(dict(view.request.data))

        with (
            patch.object(FindingViewSet, "get_object", first_read),
            patch.object(
                FindingViewSet,
                "perform_update",
                update,
            ),
            ThreadPoolExecutor(max_workers=len(changes)) as pool,
        ):
            results = list(pool.map(self.request, changes))
        self.finding.refresh_from_db()
        expected = {}
        for payload in completed:
            expected.update(payload)
        actual = {key: getattr(self.finding, key) for key in expected}
        self.record(
            {
                "concurrency": len(changes),
                "first_reads_barrier": True,
                "http_statuses": [r[0] for r in results],
                "save_completion_order": completed,
                "expected": expected,
                "actual": actual,
                "semantics": "last serialized write wins per supplied field",
            },
        )
        self.assertEqual([r[0] for r in results], [200] * len(changes))
        self.assertEqual(actual, expected)

    def test_two_disjoint_fields(self):
        self.concurrent([{"description": "New description"}, {"mitigation": "New mitigation"}])

    def test_same_field(self):
        self.concurrent([{"description": "Writer one"}, {"description": "Writer two"}])

    def burst(self, count):
        fields = ["description", "mitigation", "impact", "references", "steps_to_reproduce"]
        self.concurrent([{fields[i % len(fields)]: f"Writer {i}"} for i in range(count)])

    def test_five_patches(self):
        self.burst(5)

    def test_ten_patches(self):
        self.burst(10)

    def test_twenty_five_patches(self):
        self.burst(25)

    def test_unspecified_field(self):
        status, _ = self.request({"description": "New description"})
        self.finding.refresh_from_db()
        self.assertEqual(status, 200)
        self.assertEqual(self.finding.description, "New description")
        self.assertEqual(self.finding.mitigation, "Original mitigation")

    def test_outsider(self):
        outsider = Dojo_User.objects.create(username="rc5_outsider_" + self.suffix)
        status, _ = self.request({"description": "Forbidden"}, user_id=outsider.pk)
        self.assertIn(status, [403, 404])
        self.finding.refresh_from_db()
        self.assertEqual(self.finding.description, "Original description")

    def test_patch_with_read(self):
        barrier = threading.Barrier(2)

        def operation(method):
            barrier.wait(timeout=20)
            return self.request({"description": "Updated"} if method == "patch" else {}, method)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(operation, ["patch", "get"]))
        self.assertEqual([r[0] for r in results], [200, 200])
        self.assertIn(results[1][1]["description"], ["Original description", "Updated"])
        self.finding.refresh_from_db()
        self.assertEqual(self.finding.description, "Updated")

    def import_options(self):
        return {
            "user": self.user,
            "lead": self.user,
            "scan_date": None,
            "active": True,
            "verified": False,
            "environment": Development_Environment.objects.get_or_create(name="Development")[0],
            "scan_type": "Generic Findings Import",
            "close_old_findings": False,
            "deduplication_execution_mode": "sync",
        }

    def report(self, component=None):
        finding = {
            "title": "RC5 reimport " + self.suffix,
            "severity": "High",
            "description": "Scanner description",
            "mitigation": "Scanner mitigation",
            "cwe": 79,
        }
        if component:
            finding["component_name"] = component
        return SimpleUploadedFile("report.json", json.dumps({"findings": [finding]}).encode())

    def test_reimport_preserves_independent_patch(self):
        self.addCleanup(self.clean_imports)
        with impersonate(self.user):
            target, *_ = DefaultImporter(engagement=self.engagement, **self.import_options()).process_scan(
                self.report(),
            )
        imported = Finding.objects.get(test=target)
        self.url = reverse("finding-detail", args=[imported.pk])
        ready, resume = threading.Event(), threading.Event()
        real_match = DefaultReImporter.process_matched_finding
        sql_trace = []
        paused_state = {}

        def trace(execute, sql, params, many, context):
            if sql.startswith('UPDATE "dojo_finding"') or ('FROM "dojo_finding"' in sql):
                sql_trace.append({"sql": sql, "params": params, "in_atomic_block": connection.in_atomic_block})
            return execute(sql, params, many, context)

        def pause_after_match(importer, unsaved, existing):
            if existing.pk == imported.pk:
                paused_state.update(
                    {
                        "service": existing.service,
                        "deferred_fields": sorted(existing.get_deferred_fields()),
                        "autocommit": connection.get_autocommit(),
                        "in_atomic_block": connection.in_atomic_block,
                    },
                )
                ready.set()
                if not resume.wait(30):
                    message = "reimport did not receive resume"
                    raise AssertionError(message)
            return real_match(importer, unsaved, existing)

        def reimport():
            close_old_connections()
            try:
                with impersonate(self.user), connection.execute_wrapper(trace):
                    return (
                        DefaultReImporter(test=Test.objects.get(pk=target.pk), **self.import_options())
                        .process_scan(
                            self.report(component="new-scanner-component"),
                        )[0]
                        .pk
                    )
            finally:
                connections.close_all()

        with (
            patch.object(DefaultReImporter, "process_matched_finding", pause_after_match),
            ThreadPoolExecutor(max_workers=1) as pool,
        ):
            pending = pool.submit(reimport)
            try:
                self.assertTrue(ready.wait(30), "real reimport never matched target")
                status, _ = self.request({"service": "user-service-must-survive"})
                before = Finding.objects.get(pk=imported.pk).service
            finally:
                resume.set()
            reimport_test = pending.result(timeout=45)
        imported.refresh_from_db()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pgh_id,pgh_label,service,component_name FROM dojo_findingevent WHERE pgh_obj_id=%s ORDER BY pgh_id",
                [imported.pk],
            )
            audit = [dict(zip([c[0] for c in cursor.description], row, strict=True)) for row in cursor.fetchall()]
        self.record(
            {
                "patch_http_status": status,
                "reimport_test": reimport_test,
                "after_http": before,
                "after_reimport": imported.service,
                "scanner_component": imported.component_name,
                "same_finding_id": imported.pk,
                "expected": "user-service-must-survive",
                "pause": "after real candidate load, before real process_matched_finding",
                "paused_reimport_state": paused_state,
                "reimport_sql": sql_trace,
                "audit_history": audit,
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(imported.component_name, "new-scanner-component")
        self.assertEqual(imported.service, "user-service-must-survive")

    def test_reimport_serial_control(self):
        self.addCleanup(self.clean_imports)
        with impersonate(self.user):
            target, *_ = DefaultImporter(engagement=self.engagement, **self.import_options()).process_scan(
                self.report(),
            )
        imported = Finding.objects.get(test=target)
        self.url = reverse("finding-detail", args=[imported.pk])
        status, _ = self.request({"service": "user-service-must-survive"})
        with impersonate(self.user):
            DefaultReImporter(test=target, **self.import_options()).process_scan(
                self.report(component="new-scanner-component"),
            )
        imported.refresh_from_db()
        self.record(
            {
                "patch_http_status": status,
                "after_serial_reimport": imported.service,
                "scanner_component": imported.component_name,
                "same_finding_id": imported.pk,
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(imported.component_name, "new-scanner-component")
        self.assertEqual(imported.service, "user-service-must-survive")

    def clean_imports(self):
        from dojo.finding.helper import bulk_delete_findings  # noqa: PLC0415 -- scenario-local import

        bulk_delete_findings(Finding.objects.filter(test__engagement=self.engagement).exclude(test=self.test))
        Test.objects.filter(engagement=self.engagement).exclude(pk=self.test.pk).delete()

    def test_async_dedup_preserves_independent_patch(self):
        original, duplicate = self._create_findings("RC5 original", "RC5 original")
        Finding.objects.filter(pk__in=[original.pk, duplicate.pk]).update(hash_code="rc5-" + self.suffix)
        self.url = reverse("finding-detail", args=[original.pk])
        from dojo.finding import deduplication  # noqa: PLC0415 -- scenario-local import

        real_set = deduplication.set_duplicate
        ready, resume = threading.Event(), threading.Event()

        def pause_before_save(new, existing, **kwargs):
            if existing.pk == original.pk and new.pk == duplicate.pk:
                ready.set()
                if not resume.wait(30):
                    message = "worker did not receive resume"
                    raise AssertionError(message)
            return real_set(new, existing, **kwargs)

        previous = System_Settings.objects.get(no_cache=True).enable_deduplication
        System_Settings.objects.filter().update(enable_deduplication=True)
        self.addCleanup(lambda: System_Settings.objects.filter().update(enable_deduplication=previous))
        from dojo.caching import reset_l1_cache  # noqa: PLC0415 -- scenario-local import

        reset_l1_cache()
        queue = "rc5-" + self.suffix
        with (
            self.settings(DEDUPLICATION_ALGORITHM_PER_PARSER={self.test.test_type.name: "hash_code"}),
            patch.object(deduplication, "set_duplicate", pause_before_save),
            start_worker(
                app,
                pool="solo",
                concurrency=1,
                perform_ping_check=False,
                queues=[queue],
                shutdown_timeout=15,
            ),
        ):
            task = do_dedupe_finding_task.apply_async(args=[duplicate.pk], queue=queue, ignore_result=False)
            try:
                self.assertTrue(ready.wait(30), "broker-delivered dedup never matched original")
                status, _ = self.request({"service": "user-service-after-worker-read"})
                after_http = Finding.objects.get(pk=original.pk).service
            finally:
                resume.set()
            task.get(timeout=40, disable_sync_subtasks=False)
        original.refresh_from_db()
        duplicate.refresh_from_db()
        self.record(
            {
                "real_broker": app.conf.broker_url.split("://")[0],
                "task_id": task.id,
                "task_state": task.state,
                "patch_http_status": status,
                "after_http": after_http,
                "after_worker": original.service,
                "duplicate": duplicate.duplicate,
                "duplicate_finding_id": duplicate.duplicate_finding_id,
                "expected": "user-service-after-worker-read",
                "pause": "real set_duplicate before real database saves",
            },
        )
        self.assertEqual(status, 200)
        self.assertTrue(duplicate.duplicate)
        self.assertEqual(duplicate.duplicate_finding_id, original.pk)
        self.assertEqual(original.service, "user-service-after-worker-read")
