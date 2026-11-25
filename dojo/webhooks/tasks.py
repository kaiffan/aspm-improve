import logging
import random
import time
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Min, Q
from django.utils import timezone

from dojo.aspm_ingestion.tasks import job_lock
from dojo.celery import app
from dojo.utils import prepare_for_view
from dojo.webhooks.metrics import ATTEMPTS, DURATION, EXPANDED, OLDEST, PENDING
from dojo.webhooks.models import WebhookAttempt, WebhookDelivery, WebhookEvent, WebhookSubscription
from dojo.webhooks.services import wire_payload
from dojo.webhooks.transport import DeliveryError, send
from dojo.webhooks.validation import matches

logger = logging.getLogger(__name__)
ACTIVE = [WebhookDelivery.State.PENDING, WebhookDelivery.State.RETRY, WebhookDelivery.State.IN_FLIGHT]


def dispatch_webhooks():
    if not settings.ASPM_WEBHOOKS_ENABLED:
        return
    with transaction.atomic():
        events = list(WebhookEvent.objects.select_for_update(skip_locked=True).filter(expanded=False).order_by("occurred_at")[:100])
        target_ids = {int(pk) for event in events for pk in event.subscribers}
        subs = {sub.pk: sub for sub in WebhookSubscription.objects.select_for_update().filter(pk__in=target_ids, enabled=True, archived=False).order_by("pk")}
        pending = {row["subscription_id"]: row["total"] for row in WebhookDelivery.objects.filter(subscription_id__in=subs, state__in=ACTIVE).values("subscription_id").annotate(total=Count("pk"))}
        deliveries = []
        for event in events:
            for identifier, revision in event.subscribers.items():
                sub = subs.get(int(identifier))
                if not sub or sub.product_id != event.product_id or sub.revision != revision or (event.event_type != "webhook.test" and not matches(sub.filters, event.payload)):
                    continue
                full = pending.get(sub.pk, 0) >= settings.ASPM_WEBHOOK_MAX_PENDING
                deliveries.append(WebhookDelivery(event=event, subscription=sub, revision=sub.revision,
                    state=WebhookDelivery.State.DEAD if full else WebhookDelivery.State.PENDING, last_error="capacity_limit" if full else ""))
                pending[sub.pk] = pending.get(sub.pk, 0) + (0 if full else 1)
        WebhookDelivery.objects.bulk_create(deliveries, batch_size=500, ignore_conflicts=True)
        WebhookEvent.objects.filter(pk__in=[event.pk for event in events]).update(expanded=True)
        due = list(WebhookDelivery.objects.select_for_update(skip_locked=True).filter(Q(dispatch_until__isnull=True) | Q(dispatch_until__lte=timezone.now()), state__in=ACTIVE, next_attempt_at__lte=timezone.now()).order_by("next_attempt_at").values_list("pk", flat=True)[:100])
        WebhookDelivery.objects.filter(pk__in=due).update(dispatch_until=timezone.now() + timedelta(seconds=120))
    EXPANDED.inc(len(events))
    backlog = WebhookDelivery.objects.filter(state__in=ACTIVE).aggregate(total=Count("pk"), oldest=Min("created_at"))
    PENDING.set(backlog["total"])
    OLDEST.set(max(0, (timezone.now() - backlog["oldest"]).total_seconds()) if backlog["oldest"] else 0)
    for identifier in due:
        try:
            deliver_webhook.apply_async(args=[str(identifier)])
        except Exception:
            logger.warning("ASPM webhook broker dispatch deferred delivery_id=%s", identifier)


@app.task(name="dojo.webhooks.deliver", acks_late=True, reject_on_worker_lost=True, soft_time_limit=65, time_limit=75, ignore_result=True)
def deliver_webhook(identifier, **kwargs):
    if not settings.ASPM_WEBHOOKS_ENABLED:
        return
    with job_lock("webhook:" + str(identifier)) as acquired:
        if not acquired:
            return
        with transaction.atomic():
            subscription_id = WebhookDelivery.objects.values_list("subscription_id", flat=True).get(pk=identifier)
            sub = WebhookSubscription.objects.select_for_update().get(pk=subscription_id)
            row = WebhookDelivery.objects.select_for_update(of=("self",)).select_related("event").get(pk=identifier)
            if row.state not in ACTIVE or row.next_attempt_at > timezone.now():
                return
            if not sub.enabled or sub.archived or sub.revision != row.revision:
                row.state = WebhookDelivery.State.CANCELLED
                row.last_error = "subscription_revoked"
                row.save(update_fields=["state", "last_error"])
                return
            if sub.next_send_at > timezone.now():
                row.next_attempt_at = sub.next_send_at
                row.dispatch_until = None
                row.save(update_fields=["next_attempt_at", "dispatch_until"])
                return
            sub.next_send_at = timezone.now() + timedelta(seconds=60 / sub.rate_per_minute)
            sub.save(update_fields=["next_send_at"])
            if row.cycle_attempts >= sub.max_attempts:
                row.state = WebhookDelivery.State.DEAD
                row.last_error = "recovery_limit"
                row.save(update_fields=["state", "last_error"])
                return
            row.cycle_attempts += 1
            retry_number = row.cycle_attempts
            row.attempts += 1
            row.state = WebhookDelivery.State.IN_FLIGHT
            row.next_attempt_at = timezone.now() + timedelta(seconds=120)
            row.save(update_fields=["attempts", "cycle_attempts", "state", "next_attempt_at"])
            attempt = WebhookAttempt.objects.create(delivery=row, number=row.attempts)
        start = time.monotonic()
        status = None
        error = ""
        retryable = False
        try:
            body = wire_payload(row.event)
            secret = prepare_for_view(sub.encrypted_secret)
            if not secret:
                msg = "secret_unavailable"
                raise DeliveryError(msg)
            status = send(sub.endpoint, secret, body, row.event_id, sub.timeout_seconds, delivery_id=row.pk)
            if not 200 <= status < 300:
                error = "http_" + str(status)
                retryable = status == 429 or status >= 500
        except DeliveryError as failure:
            error = str(failure)
            retryable = error in {"dns_capacity", "dns_failed", "tls_failed", "network_failed"}
        except ValidationError:
            error = "invalid_configuration_or_payload"
        except Exception:
            error = "delivery_internal_error"
            retryable = True
        success = not error
        now = timezone.now()
        with transaction.atomic():
            # A rotation/revocation during HTTP cannot retract that request; fence all future retries.
            current = WebhookSubscription.objects.select_for_update().get(pk=sub.pk)
            if success:
                state = WebhookDelivery.State.SUCCEEDED
                WebhookSubscription.objects.filter(pk=sub.pk).update(last_success_at=now)
            elif not current.enabled or current.archived or current.revision != row.revision:
                state = WebhookDelivery.State.CANCELLED
            elif retryable and retry_number < sub.max_attempts:
                state = WebhookDelivery.State.RETRY
            else:
                state = WebhookDelivery.State.DEAD
            delay = min(3600, 2 ** min(retry_number, 11)) * random.uniform(0.75, 1.25)  # noqa: S311 -- retry jitter
            WebhookDelivery.objects.filter(pk=row.pk).update(state=state, last_error=error, dispatch_until=None, next_attempt_at=now + timedelta(seconds=delay))
            WebhookAttempt.objects.filter(pk=attempt.pk).update(finished_at=now, status_code=status, error_code=error, duration_seconds=time.monotonic() - start)
        ATTEMPTS.labels(outcome="success" if success else ("retry" if state == WebhookDelivery.State.RETRY else "failed")).inc()
        DURATION.observe(time.monotonic() - start)
        logger.info("ASPM webhook event_id=%s delivery_id=%s state=%s error_code=%s", row.event_id, row.pk, state, error)
