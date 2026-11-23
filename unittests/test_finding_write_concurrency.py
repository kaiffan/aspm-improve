"""Additional committed PostgreSQL oracles; no mocked serializers or persistence."""

import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from crum import impersonate
from django.db import (
    close_old_connections,
    connection,
    connections,
    transaction,
)
from django.db.models.signals import post_save
from django.utils import timezone

from dojo.celery import app
from dojo.finding.api.views import FindingViewSet
from dojo.finding.deduplication import set_duplicate
from dojo.importers.default_importer import DefaultImporter
from dojo.importers.default_reimporter import DefaultReImporter
from dojo.models import Finding, System_Settings, Test
from unittests import finding_write_oracles as original


@contextmanager
def product_grading_enabled():
    settings = System_Settings.objects.get(no_cache=True)
    previous = settings.enable_product_grade
    settings.enable_product_grade = True
    settings.save()
    try:
        yield
    finally:
        settings.enable_product_grade = previous
        settings.save()


@app.task(name="rc5.stale_model_writer", ignore_result=False)
def stale_model_writer(pk, directory, **kwargs):
    directory = Path(directory)
    finding = Finding.objects.get(pk=pk)
    (directory / "ready").write_text(json.dumps({"pid": os.getpid(), "service": finding.service}))
    deadline = time.monotonic() + 45
    while not (directory / "resume").exists():
        if time.monotonic() > deadline:
            message = "parent did not release stale writer"
            raise TimeoutError(message)
        time.sleep(0.01)
    finding.component_name = "celery-component"
    finding.save_no_options()
    return {"pid": os.getpid(), "pk": finding.pk}


class ExtendedRaces(original.PatchRaces):
    def assert_external_write_boundary(self, expected_service):
        self.assertFalse(connection.in_atomic_block)

        def other_connection():
            with transaction.atomic():
                row = Finding.objects.select_for_update(nowait=True).get(pk=self.finding.pk)
                self.assertEqual(row.service, expected_service)

        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(self.thread, other_connection).result(timeout=10)

    def test_jira_push_runs_after_patch_commit(self):
        observed = []

        def push(finding, **kwargs):
            self.assert_external_write_boundary("committed-before-jira")
            observed.append(finding.pk)
            return True, "ok"

        with (
            patch("dojo.finding.api.serializer.jira_services.is_keep_in_sync", return_value=True),
            patch("dojo.finding.api.serializer.jira_services.push", side_effect=push),
        ):
            self.assertEqual(self.request({"service": "committed-before-jira"})[0], 200)
        self.assertEqual(observed, [self.finding.pk])

    def test_jira_failure_preserves_existing_committed_write_contract(self):
        def push(finding, **kwargs):
            self.assert_external_write_boundary("committed-with-jira-error")
            return False, "JIRA unavailable"

        with (
            patch("dojo.finding.api.serializer.jira_services.is_keep_in_sync", return_value=True),
            patch("dojo.finding.api.serializer.jira_services.push", side_effect=push),
        ):
            status, _ = self.request({"service": "committed-with-jira-error"})
        self.assertEqual(status, 400)
        self.assertEqual(Finding.objects.get(pk=self.finding.pk).service, "committed-with-jira-error")

    def test_tool_integration_runs_after_patch_commit(self):
        observed = []

        def update(finding):
            self.assert_external_write_boundary("committed-before-tool")
            observed.append(finding.pk)

        with (
            patch("dojo.finding.helper.tool_issue_updater.is_tool_issue_updater_needed", return_value=True),
            patch("dojo.finding.helper.tool_issue_updater.async_tool_issue_update", side_effect=update),
        ):
            self.assertEqual(self.request({"service": "committed-before-tool"})[0], 200)
        self.assertEqual(observed, [self.finding.pk])

    def test_product_grade_dispatch_runs_after_patch_commit(self):
        observed = []

        def grade(product_id):
            self.assert_external_write_boundary("grade-after-commit")
            observed.append(product_id)

        with (
            product_grading_enabled(),
            patch("dojo.finding.helper.schedule_product_grade", side_effect=grade),
        ):
            self.assertEqual(self.request({"service": "grade-after-commit"})[0], 200)
        self.assertEqual(observed, [self.product.pk])

    def test_product_grade_respects_callers_outer_transaction(self):
        from dojo.finding.services import update_finding  # noqa: PLC0415 -- exercise public service

        observed = []

        def grade(product_id):
            self.assert_external_write_boundary("outer-grade-commit")
            observed.append(product_id)

        with (
            product_grading_enabled(),
            patch("dojo.finding.helper.schedule_product_grade", side_effect=grade),
            transaction.atomic(),
        ):
            update_finding(self.finding, changes={"service": "outer-grade-commit"}, user=self.user)
            self.assertEqual(observed, [])
        self.assertEqual(observed, [self.product.pk])

    def test_product_grade_is_discarded_on_outer_rollback(self):
        observed = []
        with (
            product_grading_enabled(),
            patch("dojo.finding.helper.schedule_product_grade", side_effect=observed.append),
        ):
            with self.assertRaisesMessage(RuntimeError, "rollback grade"), transaction.atomic():
                self.finding.service = "never-grade-committed"
                self.finding.save(dedupe_option=False)
                self.assertEqual(observed, [])
                message = "rollback grade"
                raise RuntimeError(message)
            self.assertEqual(observed, [])
        self.assertNotEqual(Finding.objects.get(pk=self.finding.pk).service, "never-grade-committed")

    def test_v3_integrations_respect_callers_outer_transaction(self):
        from dojo.finding.services import update_finding  # noqa: PLC0415 -- exercise public service

        observed = []

        def update(finding):
            self.assert_external_write_boundary("outer-transaction")
            observed.append(finding.pk)

        with (
            patch("dojo.finding.helper.tool_issue_updater.is_tool_issue_updater_needed", return_value=True),
            patch("dojo.finding.helper.tool_issue_updater.async_tool_issue_update", side_effect=update),
            transaction.atomic(),
        ):
            update_finding(self.finding, changes={"service": "outer-transaction"}, user=self.user)
            self.assertEqual(observed, [])
        self.assertEqual(observed, [self.finding.pk])

    def test_model_external_effect_is_discarded_on_outer_rollback(self):
        observed = []
        with (
            patch("dojo.finding.helper.tool_issue_updater.is_tool_issue_updater_needed", return_value=True),
            patch("dojo.finding.helper.tool_issue_updater.async_tool_issue_update", side_effect=lambda f: observed.append(f.pk)),
        ):
            with self.assertRaisesMessage(RuntimeError, "rollback integration"), transaction.atomic():
                self.finding.service = "never-committed"
                self.finding.save(dedupe_option=False)
                self.assertEqual(observed, [])
                message = "rollback integration"
                raise RuntimeError(message)
            self.assertEqual(observed, [])
        self.assertNotEqual(Finding.objects.get(pk=self.finding.pk).service, "never-committed")

    def test_v3_jira_push_respects_callers_outer_transaction(self):
        from dojo.finding.services import update_finding  # noqa: PLC0415 -- exercise public service

        observed = []

        def push(finding, **kwargs):
            self.assert_external_write_boundary("v3-jira-commit")
            observed.append(finding.pk)
            return True, "ok"

        with (
            patch("dojo.finding.services.jira_services.is_keep_in_sync", return_value=True),
            patch("dojo.finding.services.jira_services.push", side_effect=push),
            transaction.atomic(),
        ):
            update_finding(self.finding, changes={"service": "v3-jira-commit"}, user=self.user)
            self.assertEqual(observed, [])
        self.assertEqual(observed, [self.finding.pk])

    def thread(self, func):
        close_old_connections()
        try:
            return func()
        finally:
            connections.close_all()

    def imported(self):
        self.addCleanup(self.clean_imports)
        with impersonate(self.user):
            target, *_ = DefaultImporter(engagement=self.engagement, **self.import_options()).process_scan(
                self.report(),
            )
        finding = Finding.objects.get(test=target)
        self.url = __import__("django.urls", fromlist=["reverse"]).reverse("finding-detail", args=[finding.pk])
        return target, finding

    def test_stale_model_preserves_scalar_families(self):
        stale = Finding.objects.get(pk=self.finding.pk)
        changes = {
            "service": "user-service",
            "title": "User Title",
            "description": "User description",
            "severity": "Critical",
            "cwe": 89,
        }
        self.assertEqual(self.request(changes)[0], 200)
        stale.component_name = "scanner-component"
        stale.save_no_options()
        current = Finding.objects.get(pk=stale.pk)
        self.record({"expected": changes, "actual": {k: getattr(current, k) for k in changes}})
        self.assertEqual({k: getattr(current, k) for k in changes}, changes)
        self.assertEqual(current.component_name, "scanner-component")
        self.assertEqual(current.numerical_severity, Finding.get_numerical_severity("Critical"))

    def test_deferred_and_reused_model(self):
        stale = Finding.objects.only("id", "component_name").get(pk=self.finding.pk)
        self.assertEqual(self.request({"service": "first", "severity": "Critical"})[0], 200)
        stale.component_name = "component-one"
        stale.save_no_options()
        self.assertEqual(self.request({"service": "second", "cwe": 89})[0], 200)
        stale.component_version = "component-two"
        stale.save_no_options()
        current = Finding.objects.get(pk=stale.pk)
        self.assertEqual((current.service, current.severity, current.cwe), ("second", "Critical", 89))
        self.assertEqual((current.component_name, current.component_version), ("component-one", "component-two"))

    def test_explicit_narrow_write(self):
        stale = Finding.objects.get(pk=self.finding.pk)
        self.assertEqual(self.request({"service": "service", "description": "current"})[0], 200)
        stale.description = "must-not-write"
        stale.last_reviewed = timezone.now()
        stale.last_reviewed_by = self.user
        stale.save_no_options(update_fields=["last_reviewed", "last_reviewed_by", "updated"])
        stale.refresh_from_db()
        self.assertEqual((stale.service, stale.description), ("service", "current"))
        self.assertEqual(stale.last_reviewed_by_id, self.user.pk)

    def test_iterator_update_fields_preserves_explicit_intent(self):
        stale = Finding.objects.get(pk=self.finding.pk)
        self.assertEqual(self.request({"service": "independent-api-service"})[0], 200)
        stale.description = "iterator-description-must-survive"
        stale.save_no_options(update_fields=(name for name in ["description"]))
        stale.refresh_from_db()
        self.assertEqual(stale.service, "independent-api-service")
        self.assertEqual(stale.description, "iterator-description-must-survive")

    def test_patch_stale_before_reimport(self):
        target, finding = self.imported()
        ready, resume = threading.Event(), threading.Event()
        real = FindingViewSet.get_object

        def pause(view):
            obj = real(view)
            if not getattr(view, "_paused", False):
                view._paused = True
                ready.set()
                self.assertTrue(resume.wait(30))
            return obj

        with patch.object(FindingViewSet, "get_object", pause), ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(self.request, {"service": "after-reimport"})
            try:
                self.assertTrue(ready.wait(30))
                with impersonate(self.user):
                    DefaultReImporter(test=target, **self.import_options()).process_scan(
                        self.report(component="scanner"),
                    )
            finally:
                resume.set()
            self.assertEqual(pending.result(timeout=45)[0], 200)
        finding.refresh_from_db()
        self.assertEqual((finding.component_name, finding.service), ("scanner", "after-reimport"))
        self.record(
            {
                "component": finding.component_name,
                "service": finding.service,
                "ordering": "PATCH read; reimport commit; PATCH commit",
            },
        )

    def test_status_patch_before_stale_reimport(self):
        target, finding = self.imported()
        ready, resume = threading.Event(), threading.Event()
        real = DefaultReImporter.process_matched_finding

        def pause(importer, unsaved, existing):
            ready.set()
            self.assertTrue(resume.wait(30))
            return real(importer, unsaved, existing)

        def reimport():
            with impersonate(self.user):
                return DefaultReImporter(test=Test.objects.get(pk=target.pk), **self.import_options()).process_scan(
                    self.report(component="scanner"),
                )

        with (
            patch.object(DefaultReImporter, "process_matched_finding", pause),
            ThreadPoolExecutor(max_workers=1) as pool,
        ):
            pending = pool.submit(self.thread, reimport)
            try:
                self.assertTrue(ready.wait(30))
                self.assertEqual(self.request({"false_p": True, "active": False, "verified": False})[0], 200)
            finally:
                resume.set()
            pending.result(timeout=45)
        finding.refresh_from_db()
        self.assertTrue(finding.false_p)
        self.assertFalse(finding.active)
        self.assertFalse(finding.verified)
        self.assertTrue(finding.is_mitigated)
        self.assertIsNotNone(finding.mitigated)
        self.record(
            {
                k: getattr(finding, k)
                for k in ("false_p", "active", "verified", "is_mitigated", "mitigated", "component_name")
            },
        )

    def test_concurrent_statuses_are_serial(self):
        barrier = threading.Barrier(2)
        real_get, real_update = FindingViewSet.get_object, FindingViewSet.perform_update
        saved = []
        fields = ("active", "verified", "false_p", "is_mitigated", "mitigated", "mitigated_by_id")

        def first(view):
            obj = real_get(view)
            if not getattr(view, "_first", False):
                view._first = True
                barrier.wait(timeout=30)
            return obj

        def observed(view, serializer):
            real_update(view, serializer)
            row = Finding.objects.get(pk=self.finding.pk)
            saved.append({k: getattr(row, k) for k in fields})

        with (
            patch.object(FindingViewSet, "get_object", first),
            patch.object(FindingViewSet, "perform_update", observed),
            ThreadPoolExecutor(max_workers=2) as pool,
        ):
            statuses = list(
                pool.map(
                    self.request,
                    [
                        {"false_p": True, "active": False, "verified": False},
                        {"active": True, "verified": True, "false_p": False},
                    ],
                ),
            )
        current = Finding.objects.get(pk=self.finding.pk)
        self.assertEqual([s[0] for s in statuses], [200, 200])
        self.assertEqual({k: getattr(current, k) for k in fields}, saved[-1])
        if current.active:
            self.assertFalse(current.false_p)
            self.assertFalse(current.is_mitigated)
        self.record({"save_order": saved, "final": {k: getattr(current, k) for k in fields}})

    def test_different_findings_same_test_do_not_block(self):
        self._independent_findings(different_test=False)

    def test_different_findings_different_tests_do_not_block(self):
        self._independent_findings(different_test=True)

    def _independent_findings(self, different_test):
        other = self._create_findings("Independent finding")[0]
        if different_test:
            target = Test.objects.create(
                engagement=self.engagement,
                test_type=self.test.test_type,
                target_start=self.test.target_start,
                target_end=self.test.target_end,
            )
            Finding.objects.filter(pk=other.pk).update(test=target)
        acquired, release = threading.Event(), threading.Event()

        def hold():
            with transaction.atomic():
                Finding.unfiltered.select_for_update(no_key=True).get(pk=self.finding.pk)
                acquired.set()
                self.assertTrue(release.wait(30))

        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(self.thread, hold)
            try:
                self.assertTrue(acquired.wait(30))
                self.url = __import__("django.urls", fromlist=["reverse"]).reverse("finding-detail", args=[other.pk])
                self.assertEqual(self.request({"service": "independent"})[0], 200)
                self.assertFalse(pending.done())
            finally:
                release.set()
            pending.result(timeout=45)
        other.refresh_from_db()
        self.assertEqual(other.service, "independent")

    def test_timeout_rollback_and_retry(self):
        acquired, release = threading.Event(), threading.Event()

        def hold():
            with transaction.atomic():
                Finding.unfiltered.select_for_update(no_key=True).get(pk=self.finding.pk)
                acquired.set()
                self.assertTrue(release.wait(30))

        def timeout_request():
            def timeout(execute, sql, params, many, context):
                if "FOR NO KEY UPDATE" in sql or "FOR UPDATE" in sql:
                    with connection.cursor() as cursor:
                        cursor.execute("SET LOCAL lock_timeout = '100ms'")
                return execute(sql, params, many, context)

            with connection.execute_wrapper(timeout):
                result = self.request({"service": "retry"})
                self.record({"unexpected_timeout_result": result})
                return result

        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(self.thread, hold)
            try:
                self.assertTrue(acquired.wait(30))
                self.assertEqual(timeout_request()[0], 500)
            finally:
                release.set()
            pending.result(timeout=45)
        self.assertIsNone(Finding.objects.get(pk=self.finding.pk).service)
        self.assertEqual(self.request({"service": "retry"})[0], 200)
        self.assertEqual(Finding.objects.get(pk=self.finding.pk).service, "retry")

    def test_signal_and_audit_observe_merged_state(self):
        stale = Finding.objects.get(pk=self.finding.pk)
        self.assertEqual(self.request({"service": "audit-service"})[0], 200)
        observed = []

        def receiver(sender, instance, **kwargs):
            observed.append(instance.service)

        post_save.connect(receiver, sender=Finding, weak=False)
        try:
            stale.component_name = "audit-component"
            stale.save_no_options()
        finally:
            post_save.disconnect(receiver, sender=Finding)
        self.assertEqual(observed, ["audit-service"])
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT service,component_name FROM dojo_findingevent WHERE pgh_obj_id=%s ORDER BY pgh_id", [stale.pk],
            )
            history = cursor.fetchall()
        self.assertEqual(history[-1], ("audit-service", "audit-component"))
        seen = False
        for service, _component in history:
            if service == "audit-service":
                seen = True
            if seen:
                self.assertEqual(service, "audit-service")
        self.record({"post_save": observed, "audit": history})

    def test_rolled_back_model_can_retry_same_edits(self):
        finding = Finding.objects.get(pk=self.finding.pk)
        finding.service = "retry-model"
        try:
            with transaction.atomic():
                finding.save_no_options()
                message = "rollback"
                raise RuntimeError(message)
        except RuntimeError:
            pass
        self.assertIsNone(Finding.objects.get(pk=finding.pk).service)
        finding.save_no_options()
        self.assertEqual(Finding.objects.get(pk=finding.pk).service, "retry-model")

    def test_failed_signal_rolls_back_scalar_and_relations(self):
        before = Finding.objects.get(pk=self.finding.pk)

        def reject(sender, instance, **kwargs):
            if instance.pk == self.finding.pk:
                message = "injected signal failure"
                raise RuntimeError(message)

        post_save.connect(reject, sender=Finding, weak=False)
        try:
            status, _data = self.request({"service": "must-rollback", "cwes": [{"cwe": 79}, {"cwe": 89}]})
            self.assertEqual(status, 500)
        finally:
            post_save.disconnect(reject, sender=Finding)
        current = Finding.objects.get(pk=self.finding.pk)
        self.assertEqual((current.service, current.cwe), (before.service, before.cwe))
        self.assertFalse(current.finding_cwe_set.exists())

    def test_real_import_dedup_preserves_patch(self):
        _target, finding = self.imported()
        from dojo.caching import reset_l1_cache  # noqa: PLC0415 -- scenario-local import
        from dojo.finding import deduplication  # noqa: PLC0415 -- scenario-local import

        previous = System_Settings.objects.get(no_cache=True).enable_deduplication
        System_Settings.objects.filter().update(enable_deduplication=True)
        reset_l1_cache()
        self.addCleanup(lambda: System_Settings.objects.filter().update(enable_deduplication=previous))
        ready, resume = threading.Event(), threading.Event()
        real = deduplication.set_duplicate

        def pause(new, existing, **kw):
            if existing.pk == finding.pk:
                ready.set()
                self.assertTrue(resume.wait(30))
            return real(new, existing, **kw)

        def import_again():
            with impersonate(self.user):
                return (
                    DefaultImporter(engagement=self.engagement, **self.import_options())
                    .process_scan(self.report())[0]
                    .pk
                )

        with patch.object(deduplication, "set_duplicate", pause), ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(self.thread, import_again)
            try:
                self.assertTrue(ready.wait(30), "real import never reached dedup")
                self.assertEqual(self.request({"service": "import-service"})[0], 200)
            finally:
                resume.set()
            new_test = pending.result(timeout=45)
        finding.refresh_from_db()
        duplicate = Finding.objects.get(test_id=new_test)
        self.assertEqual(finding.service, "import-service")
        self.assertTrue(duplicate.duplicate)
        self.assertEqual(duplicate.duplicate_finding_id, finding.pk)

    def test_broker_process_stale_save(self):
        directory = Path("/tmp/rc5-worker-" + self.suffix)
        directory.mkdir()
        queue = "rc5-process-" + self.suffix
        env = {**os.environ, "DD_DATABASE_NAME": connection.settings_dict["NAME"]}
        log = (directory / "worker.log").open("w")
        worker = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "celery",
                "-A",
                "dojo.celery",
                "worker",
                "-P",
                "solo",
                "-c",
                "1",
                "-Q",
                queue,
                "-n",
                queue + "@%h",
                "-I",
                "unittests.test_finding_write_concurrency",
                "--loglevel",
                "WARNING",
                "--without-gossip",
                "--without-mingle",
            ],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            result = stale_model_writer.apply_async(
                args=[self.finding.pk, str(directory)], queue=queue, ignore_result=False,
            )
            deadline = time.monotonic() + 40
            while not (directory / "ready").exists():
                if worker.poll() is not None:
                    raise AssertionError((directory / "worker.log").read_text())
                if time.monotonic() > deadline:
                    raise AssertionError(
                        "separate worker never read Finding: " + (directory / "worker.log").read_text(),
                    )
                time.sleep(0.05)
            ready = json.loads((directory / "ready").read_text())
            self.assertNotEqual(ready["pid"], os.getpid())
            self.assertEqual(self.request({"service": "process-service"})[0], 200)
            (directory / "resume").touch()
            completed = result.get(timeout=40, disable_sync_subtasks=False)
            current = Finding.objects.get(pk=self.finding.pk)
            self.record(
                {
                    "worker": completed,
                    "parent_pid": os.getpid(),
                    "service": current.service,
                    "component": current.component_name,
                },
            )
            self.assertEqual(current.service, "process-service")
            self.assertEqual(current.component_name, "celery-component")
        finally:
            (directory / "resume").touch()
            worker.terminate()
            try:
                worker.wait(timeout=15)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait(timeout=5)
            log.close()

    def test_direct_dedup_persists_signal_status_timestamp(self):
        root, duplicate = self._create_findings("Direct duplicate", "Direct duplicate")
        old = timezone.now() - timedelta(days=2)
        Finding.objects.filter(pk=duplicate.pk).update(last_status_update=old)
        duplicate.refresh_from_db()
        observed = []

        def receiver(sender, instance, **kwargs):
            if instance.pk == duplicate.pk:
                observed.append(instance.last_status_update)

        post_save.connect(receiver, sender=Finding, weak=False)
        try:
            set_duplicate(duplicate, root, save=True)
        finally:
            post_save.disconnect(receiver, sender=Finding)
        duplicate.refresh_from_db()
        self.record({"before": old, "signal_value": observed[-1], "persisted": duplicate.last_status_update})
        self.assertTrue(duplicate.duplicate)
        self.assertFalse(duplicate.active)
        self.assertFalse(duplicate.verified)
        self.assertGreater(observed[-1], old)
        self.assertEqual(duplicate.last_status_update, observed[-1])
