import hashlib
import hmac
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import MagicMock, patch

import urllib3
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, TransactionTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from dojo.aspm_ingestion.models import GeneratedReport, ScanRun
from dojo.aspm_ingestion.services import finalize_commit, request_report
from dojo.aspm_ingestion.tasks import process_job
from dojo.models import Finding
from dojo.operations.middleware import OperationsMiddleware
from dojo.scm.models import Repository
from dojo.utils import prepare_for_view
from dojo.webhooks.catalog import EVENT_TYPES
from dojo.webhooks.models import WebhookAttempt, WebhookAudit, WebhookDelivery, WebhookEvent, WebhookSubscription
from dojo.webhooks.services import change_subscription, replay_delivery, save_subscription, test_event
from dojo.webhooks.tasks import deliver_webhook, dispatch_webhooks
from dojo.webhooks.transport import DeliveryError, resolve_public, send, signature
from dojo.webhooks.validation import matches, validate_endpoint, validate_rules
from unittests.test_aspm_ingestion import IngestionFixture


@override_settings(ASPM_WEBHOOKS_ENABLED=True)
class WebhookTests(IngestionFixture, APITestCase):
    def setUp(self):
        self.setup_ingestion()
        self.admin = get_user_model().objects.create_user(username="hook-admin", is_superuser=True, password=None)
        self.browser = Client()
        self.browser.force_login(self.admin)
        self.sub, self.secret = self.subscribe()

    def subscribe(self, **changes):
        values = {"product": self.product, "name": "Incident feed", "endpoint": "https://consumer.example.com/hooks", "enabled": True,
                      "events": list(EVENT_TYPES), "filters": {}, "timeout_seconds": 5, "max_attempts": 3, "rate_per_minute": 60}
        values.update(changes)
        return save_subscription(actor=self.admin, values=values)

    def pending(self):
        event = test_event(self.sub, self.admin)
        with patch("dojo.webhooks.tasks.deliver_webhook.apply_async"):
            dispatch_webhooks()
        return WebhookDelivery.objects.get(event=event, subscription=self.sub)

    def advance(self, row):
        past = timezone.now() - timedelta(seconds=1)
        WebhookSubscription.objects.filter(pk=self.sub.pk).update(next_send_at=past)
        WebhookDelivery.objects.filter(pk=row.pk).update(next_attempt_at=past, dispatch_until=None)

    def test_business_events_share_transaction_and_rollback(self):
        with self.assertRaises(ValueError), transaction.atomic():
            Repository.objects.create(product=self.product, url="https://example.com/rolled-back")
            self.assertTrue(WebhookEvent.objects.filter(event_type="repository.created").exists())
            msg = "rollback"
            raise ValueError(msg)
        self.assertFalse(WebhookEvent.objects.exists())

    def test_event_content_is_immutable(self):
        event = test_event(self.sub, self.admin)
        with self.assertRaises(IntegrityError), transaction.atomic():
            WebhookEvent.objects.filter(pk=event.pk).update(payload={"injected": True})
        event.refresh_from_db()
        self.assertNotIn("injected", event.payload)

    def test_scan_repository_commit_and_report_catalog(self):
        scan = self.accepted()
        accepted_id = WebhookEvent.objects.get(event_type="scan.accepted").pk
        self.complete(scan)
        report = request_report(scan.commit, expected_scanners=[scan.scanner])
        process_job("report", str(report.pk))
        events = set(WebhookEvent.objects.values_list("event_type", flat=True))
        self.assertTrue({"repository.created", "commit.first_seen", "scan.accepted", "scan.processing", "scan.completed", "commit.scan_completed", "report.generated", "finding.created"} <= events)
        self.assertEqual(WebhookEvent.objects.get(event_type="scan.accepted").pk, accepted_id)
        event = WebhookEvent.objects.get(event_type="scan.completed")
        self.assertEqual(event.payload["scan"]["status"], "COMPLETED")
        self.assertEqual(event.payload["correlation_id"], scan.metadata["correlation_id"])
        self.assertNotIn("description", json.dumps(event.payload))

    def test_failed_scan_and_report_events(self):
        scan = self.accepted()
        ScanRun.objects.filter(pk=scan.pk).update(status="FAILED")
        scan_set = finalize_commit(scan.commit, [scan.scanner])
        report = GeneratedReport.objects.create(commit=scan.commit, scan_set=scan_set, version=1, manifest={})
        GeneratedReport.objects.filter(pk=report.pk).update(status="FAILED")
        self.assertTrue(WebhookEvent.objects.filter(event_type="scan.failed").exists())
        self.assertTrue(WebhookEvent.objects.filter(event_type="report.failed").exists())

    def test_idempotent_upload_does_not_emit_duplicate_events(self):
        self.accepted()
        count = WebhookEvent.objects.count()
        self.assertEqual(self.upload().status_code, 200)
        self.assertEqual(WebhookEvent.objects.count(), count)

    def test_actual_finding_changes_including_queryset_update(self):
        scan = self.complete(self.accepted())
        finding = Finding.objects.get(test_id=scan.test_id)
        before = WebhookEvent.objects.count()
        Finding.objects.filter(pk=finding.pk).update(severity=finding.severity, active=finding.active)
        self.assertEqual(WebhookEvent.objects.count(), before)
        Finding.objects.filter(pk=finding.pk).update(severity="Critical", active=False, false_p=True)
        events = set(WebhookEvent.objects.values_list("event_type", flat=True))
        self.assertTrue({"finding.updated", "finding.severity_changed", "finding.status_changed", "finding.false_positive_changed"} <= events)
        self.assertNotIn("description", json.dumps(WebhookEvent.objects.get(event_type="finding.severity_changed").payload))

    def test_filters_multiple_subscriptions_and_product_isolation(self):
        matching, _ = self.subscribe(events=["scan.completed"], filters={"severity": ["High"], "scanner": ["Generic Findings Import"]})
        other, _ = self.subscribe(events=["scan.completed"], filters={"severity": ["Critical"]})
        hidden, _ = self.subscribe(product=self.hidden, events=["scan.completed"])
        self.complete(self.accepted())
        with patch("dojo.webhooks.tasks.deliver_webhook.apply_async"):
            dispatch_webhooks()
        event = WebhookEvent.objects.get(event_type="scan.completed")
        self.assertEqual(set(WebhookDelivery.objects.filter(event=event).values_list("subscription_id", flat=True)), {self.sub.pk, matching.pk})
        self.assertFalse(WebhookDelivery.objects.filter(subscription__in=[other, hidden]).exists())

    def test_subscription_scope_validation(self):
        hidden = Repository.objects.create(product=self.hidden, url="https://example.com/hidden")
        with self.assertRaises(ValidationError):
            self.subscribe(filters={"repository_id": [str(hidden.pk)]})

    def test_deliver_success_and_duplicate_no_second_request(self):
        row = self.pending()
        with patch("dojo.webhooks.tasks.send", return_value=204) as sender:
            deliver_webhook(str(row.pk))
            deliver_webhook(str(row.pk))
        row.refresh_from_db()
        self.assertEqual(row.state, "SUCCEEDED")
        self.assertEqual(row.attempts, 1)
        sender.assert_called_once()
        self.assertEqual(sender.call_args.args[1], self.secret)
        body = json.loads(sender.call_args.args[2])
        self.assertEqual(body["event_id"], str(row.event_id))
        self.assertEqual(body["event_version"], "1")
        self.sub.refresh_from_db()
        self.assertIsNotNone(self.sub.last_success_at)

    def test_http_error_policy(self):
        for status, state in [(200, "SUCCEEDED"), (400, "DEAD"), (401, "DEAD"), (429, "RETRY"), (500, "RETRY"), (301, "DEAD")]:
            with self.subTest(status=status):
                row = self.pending()
                self.advance(row)
                with patch("dojo.webhooks.tasks.send", return_value=status):
                    deliver_webhook(str(row.pk))
                row.refresh_from_db()
                self.assertEqual(row.state, state)
                attempt = row.history.get()
                self.assertEqual(attempt.status_code, status)
                self.assertIsNotNone(attempt.duration_seconds)

    def test_network_failure_retry_and_bounded_attempts(self):
        row = self.pending()
        WebhookSubscription.objects.filter(pk=self.sub.pk).update(max_attempts=2)
        for expected in ("RETRY", "DEAD"):
            self.advance(row)
            with patch("dojo.webhooks.tasks.send", side_effect=DeliveryError("network_failed")):
                deliver_webhook(str(row.pk))
            row.refresh_from_db()
            self.assertEqual(row.state, expected)
        self.assertEqual(row.history.count(), 2)
        with patch("dojo.webhooks.tasks.send") as sender:
            deliver_webhook(str(row.pk))
        sender.assert_not_called()

    def test_safe_transport_error_codes(self):
        for error, expected in [("dns_failed", "RETRY"), ("tls_failed", "RETRY"), ("ssrf_blocked", "DEAD")]:
            with self.subTest(error=error):
                row = self.pending()
                self.advance(row)
                with patch("dojo.webhooks.tasks.send", side_effect=DeliveryError(error)):
                    deliver_webhook(str(row.pk))
                row.refresh_from_db()
                self.assertEqual(row.state, expected)
                self.assertEqual(row.last_error, error)

    def test_backoff_blocks_early_broker_duplicate(self):
        row = self.pending()
        with patch("dojo.webhooks.tasks.send", return_value=500) as sender:
            deliver_webhook(str(row.pk))
            deliver_webhook(str(row.pk))
        self.assertEqual(sender.call_count, 1)

    def test_manual_replay_preserves_event_and_attempt_history(self):
        row = self.pending()
        with patch("dojo.webhooks.tasks.send", return_value=400):
            deliver_webhook(str(row.pk))
        event_id = row.event_id
        replay_delivery(row, self.admin)
        self.advance(row)
        with patch("dojo.webhooks.tasks.send", return_value=200):
            deliver_webhook(str(row.pk))
        row.refresh_from_db()
        self.assertEqual(row.state, "SUCCEEDED")
        self.assertEqual(row.event_id, event_id)
        self.assertEqual(list(row.history.order_by("number").values_list("number", flat=True)), [1, 2])
        self.assertEqual(row.cycle_attempts, 1)

    def test_rotation_revocation_and_disabled_subscriptions(self):
        for action in ("rotate", "disable", "archive"):
            with self.subTest(action=action):
                sub, _ = self.subscribe()
                event = test_event(sub, self.admin)
                with patch("dojo.webhooks.tasks.deliver_webhook.apply_async"):
                    dispatch_webhooks()
                row = WebhookDelivery.objects.get(event=event)
                raw = change_subscription(sub, self.admin, action)
                if action == "rotate":
                    sub.refresh_from_db()
                    self.assertEqual(prepare_for_view(sub.encrypted_secret), raw)
                with patch("dojo.webhooks.tasks.send") as sender:
                    deliver_webhook(str(row.pk))
                sender.assert_not_called()
                row.refresh_from_db()
                self.assertEqual(row.state, "CANCELLED")

    def test_worker_recovery_uses_durable_delivery(self):
        row = self.pending()
        WebhookDelivery.objects.filter(pk=row.pk).update(state="IN_FLIGHT", attempts=1, cycle_attempts=1)
        WebhookAttempt.objects.create(delivery=row, number=1)
        self.advance(row)
        with patch("dojo.webhooks.tasks.send", return_value=200):
            deliver_webhook(str(row.pk))
        row.refresh_from_db()
        self.assertEqual(row.state, "SUCCEEDED")
        self.assertEqual(row.history.count(), 2)
        self.assertIsNone(row.history.get(number=1).finished_at)

    def test_broker_outage_recovery_and_idempotent_fanout(self):
        row = self.pending()
        self.advance(row)
        with patch("dojo.webhooks.tasks.deliver_webhook.apply_async", side_effect=OSError("broker unavailable")):
            dispatch_webhooks()
        self.assertTrue(WebhookDelivery.objects.filter(pk=row.pk, state="PENDING").exists())
        self.advance(row)
        with patch("dojo.webhooks.tasks.deliver_webhook.apply_async") as sender:
            dispatch_webhooks()
        sender.assert_called_once()
        self.assertEqual(WebhookDelivery.objects.filter(event=row.event).count(), 1)

    @override_settings(ASPM_WEBHOOK_MAX_PENDING=1)
    def test_capacity_limit_is_visible_without_rollback_of_scan(self):
        first = self.pending()
        second = test_event(self.sub, self.admin)
        with patch("dojo.webhooks.tasks.deliver_webhook.apply_async"):
            dispatch_webhooks()
        row = WebhookDelivery.objects.get(event=second)
        self.assertEqual(row.state, "DEAD")
        self.assertEqual(row.last_error, "capacity_limit")
        self.assertEqual(self.accepted().status, "ACCEPTED")
        self.assertTrue(WebhookDelivery.objects.filter(pk=first.pk).exists())

    def test_payload_limit_and_secret_not_exposed(self):
        row = self.pending()
        with override_settings(ASPM_WEBHOOK_MAX_PAYLOAD_BYTES=10), patch("dojo.webhooks.tasks.send") as sender:
            deliver_webhook(str(row.pk))
        sender.assert_not_called()
        row.refresh_from_db()
        self.assertEqual(row.state, "DEAD")
        for url in (reverse("aspm_webhooks"), reverse("aspm_webhook_edit", args=[self.sub.pk]), reverse("aspm_webhook_history", args=[self.sub.pk]), reverse("aspm_webhook_attempts", args=[self.sub.pk, row.pk])):
            response = self.browser.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, self.secret)
            self.assertNotContains(response, self.sub.encrypted_secret)
            self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_user_staff_and_viewer_cannot_manage(self):
        for staff in (False, True):
            get_user_model().objects.filter(pk=self.service.pk).update(is_staff=staff)
            self.service.refresh_from_db()
            self.browser.force_login(self.service)
            for url in (reverse("aspm_webhooks"), reverse("aspm_webhook_edit", args=[self.sub.pk]), reverse("aspm_webhook_history", args=[self.sub.pk])):
                self.assertEqual(self.browser.get(url).status_code, 403)
            self.assertEqual(self.browser.post(reverse("aspm_webhook_action", args=[self.sub.pk, "rotate"])).status_code, 403)

    def test_explicit_platform_capability_does_not_require_staff(self):
        permission = Permission.objects.get(codename="manage_outbound_webhooks")
        self.service.user_permissions.add(permission)
        self.browser.force_login(self.service)
        self.assertEqual(self.browser.get(reverse("aspm_webhooks")).status_code, 200)

    def test_mutations_require_post_and_csrf(self):
        url = reverse("aspm_webhook_action", args=[self.sub.pk, "rotate"])
        self.assertEqual(self.browser.get(url).status_code, 405)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.admin)
        self.assertEqual(strict.post(url).status_code, 403)

    def test_ui_creation_secret_once_and_audit(self):
        data = {"name": "UI hook", "product_id": self.product.pk, "endpoint": "https://consumer.example.com/hooks", "enabled": "on", "events": ["scan.completed"], "timeout_seconds": 5, "max_attempts": 4, "rate_per_minute": 10}
        response = self.browser.post(reverse("aspm_webhook_new"), data)
        self.assertEqual(response.status_code, 200)
        sub = WebhookSubscription.objects.get(name="UI hook")
        raw = prepare_for_view(sub.encrypted_secret)
        self.assertContains(response, raw)
        self.assertNotContains(self.browser.get(reverse("aspm_webhook_edit", args=[sub.pk])), raw)
        self.assertTrue(WebhookAudit.objects.filter(subscription=sub, action="created", actor=self.admin).exists())

    def test_validate_configuration_does_not_create_subscription(self):
        count = WebhookSubscription.objects.count()
        response = self.browser.post(reverse("aspm_webhook_new"), {"name": "Validate only", "product_id": self.product.pk, "endpoint": "https://consumer.example.com/events", "events": ["scan.completed"], "timeout_seconds": 5, "max_attempts": 4, "rate_per_minute": 10, "intent": "validate"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(WebhookSubscription.objects.count(), count)
        self.assertContains(response, "Configuration is valid")

    def test_durable_metrics_are_observable_from_another_process(self):
        from dojo.webhooks.metrics import DurableOutboxCollector  # noqa: PLC0415 -- collector setup

        self.pending()
        metrics = {metric.name: metric for metric in DurableOutboxCollector().collect()}
        self.assertEqual(metrics["aspm_webhook_outbox_pending"].samples[0].value, 1)
        self.assertEqual(metrics["aspm_outbox_metrics_available"].samples[0].value, 1)

    def test_large_event_fanout_has_bounded_batches_and_queries(self):
        WebhookEvent.objects.bulk_create([WebhookEvent(product=self.product, event_type="webhook.test", payload={"attributes": {}}, subscribers={str(self.sub.pk): self.sub.revision}) for _ in range(1000)])
        counts = []
        for expected in (100, 200):
            with CaptureQueriesContext(connection) as captured, patch("dojo.webhooks.tasks.deliver_webhook.apply_async"):
                dispatch_webhooks()
            counts.append(len(captured))
            self.assertEqual(WebhookDelivery.objects.count(), expected)
        self.assertLessEqual(max(counts), 15)
        self.assertLessEqual(abs(counts[0] - counts[1]), 1)
        self.assertEqual(WebhookEvent.objects.filter(expanded=False).count(), 800)


@override_settings(ASPM_WEBHOOKS_ENABLED=True)
class WebhookConcurrentFindingTests(IngestionFixture, TransactionTestCase):
    def setUp(self):
        self.setup_ingestion()
        self.admin = get_user_model().objects.create_user(username="race-hook-admin", is_superuser=True, password=None)
        save_subscription(actor=self.admin, values={"product": self.product, "name": "Race feed", "endpoint": "https://consumer.example.com/hooks", "enabled": True, "events": ["finding.updated", "finding.severity_changed", "finding.false_positive_changed"], "filters": {}, "timeout_seconds": 5, "max_attempts": 3, "rate_per_minute": 60})

    def test_concurrent_independent_updates_capture_actual_changes(self):
        scan = self.complete(self.accepted())
        finding = Finding.objects.get(test_id=scan.test_id)
        barrier = Barrier(2)

        def update(values):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                Finding.objects.filter(pk=finding.pk).update(**values)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(update, values) for values in ({"severity": "Critical"}, {"false_p": True})]
            for future in futures:
                future.result(timeout=20)
        finding.refresh_from_db()
        self.assertEqual(finding.severity, "Critical")
        self.assertTrue(finding.false_p)
        self.assertEqual(WebhookEvent.objects.filter(event_type="finding.severity_changed").count(), 1)
        self.assertEqual(WebhookEvent.objects.filter(event_type="finding.false_positive_changed").count(), 1)
        self.assertEqual(WebhookEvent.objects.filter(event_type="finding.updated").count(), 2)


class WebhookTransportTests(SimpleTestCase):
    def test_endpoint_policy(self):
        for endpoint in ("http://example.com/", "https://127.0.0.1/", "https://169.254.169.254/", "https://10.0.0.1/", "https://user:secret@example.com/", "https://example.com/?token=secret", "https://example.com/#x", "https://example.com:444/", "https://example.com/\r\nInjected: true"):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValidationError):
                validate_endpoint(endpoint)
        self.assertEqual(validate_endpoint("https://consumer.example.com/events"), "https://consumer.example.com/events")

    def test_dns_private_mixed_and_rebinding_are_blocked(self):
        for addresses in (["127.0.0.1"], ["10.0.0.1"], ["169.254.169.254"], ["93.184.216.34", "192.168.1.1"], ["::1"], ["224.0.0.1"], ["ff02::1"], ["64:ff9b::7f00:1"]):
            with self.subTest(addresses=addresses), patch("dojo.webhooks.transport.socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443)) for ip in addresses]), self.assertRaises(DeliveryError):
                resolve_public("consumer.example.com")

    def test_dns_and_tls_failures_are_safe(self):
        with patch("dojo.webhooks.transport.socket.getaddrinfo", side_effect=socket.gaierror("sensitive-host")), self.assertRaisesRegex(DeliveryError, "dns_failed"):
            resolve_public("consumer.example.com")
        with patch("dojo.webhooks.transport.resolve_public", return_value="93.184.216.34"), patch("dojo.webhooks.transport.urllib3.HTTPSConnectionPool") as pool:
            pool.return_value.__enter__.return_value.urlopen.side_effect = urllib3.exceptions.SSLError("sensitive certificates")
            with self.assertRaisesRegex(DeliveryError, "tls_failed"):
                send("https://consumer.example.com/", "secret", b"{}", "event-id", 2, delivery_id="delivery-id")

    def test_pinned_ip_hostname_tls_no_redirect_no_body_read(self):
        response = MagicMock(status=302)
        with patch("dojo.webhooks.transport.resolve_public", return_value="93.184.216.34"), patch("dojo.webhooks.transport.urllib3.HTTPSConnectionPool") as pool:
            client = pool.return_value.__enter__.return_value
            client.urlopen.return_value = response
            self.assertEqual(send("https://consumer.example.com/events", "secret", b"{}", "event-id", 2, delivery_id="delivery-id"), 302)
            self.assertEqual(pool.call_args.args[0], "93.184.216.34")
            self.assertEqual(pool.call_args.kwargs["assert_hostname"], "consumer.example.com")
            self.assertEqual(pool.call_args.kwargs["server_hostname"], "consumer.example.com")
            self.assertEqual(pool.call_args.kwargs["cert_reqs"], "CERT_REQUIRED")
            self.assertFalse(client.urlopen.call_args.kwargs["redirect"])
            self.assertFalse(client.urlopen.call_args.kwargs["preload_content"])
            self.assertFalse(client.urlopen.call_args.kwargs["retries"])
            response.read.assert_not_called()
            response.close.assert_called_once()

    def test_hmac_is_timestamp_and_exact_body_bound(self):
        expected = "v1=" + hmac.new(b"secret", b"123.{}", hashlib.sha256).hexdigest()
        self.assertEqual(signature("secret", 123, b"{}"), expected)
        self.assertNotEqual(signature("secret", 124, b"{}"), expected)
        self.assertNotEqual(signature("secret", 123, b"{ }"), expected)

    def test_filter_semantics(self):
        validate_rules(["scan.completed"], {"severity": ["Critical", "High"], "repository_id": ["10"]})
        self.assertTrue(matches({"severity": ["Critical", "High"], "repository_id": ["10"]}, {"attributes": {"severity": ["High", "Low"], "repository_id": 10}}))
        self.assertFalse(matches({"severity": ["High"]}, {"attributes": {}}))
        self.assertFalse(matches({"severity": ["High"]}, {"attributes": {"severity": []}}))
        for rules in ({"unknown": ["x"]}, {"severity": ["Severe"]}, {"scanner": "Generic"}, {"repository_id": ["../x"]}):
            with self.subTest(rules=rules), self.assertRaises(ValidationError):
                validate_rules(["scan.completed"], rules)


class OperationalProbeTests(SimpleTestCase):
    def test_liveness_and_startup_do_not_touch_dependencies(self):
        for endpoint in ("/health/live", "/health/startup"):
            with patch("dojo.operations.health.database_ready", side_effect=AssertionError("DB touched")), patch("dojo.operations.health.redis_ready", side_effect=AssertionError("broker touched")):
                response = OperationsMiddleware(lambda _request: HttpResponse("unexpected"))(RequestFactory().get(endpoint))
                self.assertEqual(response.status_code, 200)

    def test_readiness_failure_is_503_without_secret_details(self):
        with patch("dojo.operations.health.database_ready", side_effect=OSError("password=secret")):
            response = OperationsMiddleware(lambda _request: HttpResponse())(RequestFactory().get("/health/ready"))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"secret", response.content)

    def test_valid_correlation_id_and_generated_fallback(self):
        middleware = OperationsMiddleware(lambda _request: HttpResponse())
        valid = middleware(RequestFactory().get("/other", HTTP_X_CORRELATION_ID="pipeline-123"))
        self.assertEqual(valid["X-Correlation-ID"], "pipeline-123")
        generated = middleware(RequestFactory().get("/other", HTTP_X_CORRELATION_ID="unsafe header value"))
        self.assertEqual(len(generated["X-Correlation-ID"]), 32)
