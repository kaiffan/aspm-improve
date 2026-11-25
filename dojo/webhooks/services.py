import json
import secrets

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from dojo.scm.models import Repository
from dojo.utils import dojo_crypto_encrypt
from dojo.webhooks.models import WebhookAudit, WebhookDelivery, WebhookEvent, WebhookSubscription
from dojo.webhooks.permissions import can_manage_webhooks
from dojo.webhooks.validation import validate_endpoint, validate_rules


def require_manager(user):
    if not can_manage_webhooks(user):
        raise PermissionDenied


def encrypted_secret():
    raw = secrets.token_urlsafe(32)
    return raw, dojo_crypto_encrypt(raw)


def validate_configuration(*, actor, values, subscription=None):
    require_manager(actor)
    validate_endpoint(values["endpoint"])
    validate_rules(values["events"], values["filters"])
    if not 1 <= values["timeout_seconds"] <= 30 or not 1 <= values["max_attempts"] <= 12 or not 1 <= values["rate_per_minute"] <= 600:
        msg = "Invalid timeout, retry or rate limit."
        raise ValidationError(msg)
    product = values["product"]
    repository_ids = values["filters"].get("repository_id", [])
    if repository_ids and Repository.objects.filter(pk__in=repository_ids, product=product).count() != len(set(repository_ids)):
        msg = "Every filtered repository must belong to the selected Product."
        raise ValidationError(msg)
    if subscription and subscription.product_id != product.pk:
        msg = "Create a new subscription to change Product scope."
        raise ValidationError(msg)


@transaction.atomic
def save_subscription(*, actor, values, subscription=None):
    require_manager(actor)
    validate_configuration(actor=actor, values=values, subscription=subscription)
    product = values["product"]
    # Lock the Product row to serialize subscription admission, not business transactions.
    type(product).objects.select_for_update().get(pk=product.pk)
    if subscription is None and WebhookSubscription.objects.filter(product=product, archived=False).count() >= 100:
        msg = "At most 100 subscriptions per Product."
        raise ValidationError(msg)
    if subscription:
        subscription = WebhookSubscription.objects.select_for_update().get(pk=subscription.pk, archived=False)
        if subscription.product_id != product.pk:
            msg = "Create a new subscription to change Product scope."
            raise ValidationError(msg)
        subscription.revision += 1
        raw = None
    else:
        raw, encrypted = encrypted_secret()
        subscription = WebhookSubscription(encrypted_secret=encrypted)
    for field in ("name", "product", "endpoint", "events", "filters", "enabled", "timeout_seconds", "max_attempts", "rate_per_minute"):
        setattr(subscription, field, values[field])
    subscription.save()
    WebhookAudit.objects.create(subscription=subscription, actor=actor, action="updated" if raw is None else "created")
    return subscription, raw


@transaction.atomic
def change_subscription(subscription, actor, action):
    require_manager(actor)
    sub = WebhookSubscription.objects.select_for_update().get(pk=subscription.pk, archived=False)
    raw = None
    if action == "rotate":
        raw, sub.encrypted_secret = encrypted_secret()
    elif action == "disable":
        sub.enabled = False
    elif action == "archive":
        sub.enabled = False
        sub.archived = True
    else:
        msg = "Unknown action."
        raise ValidationError(msg)
    sub.revision += 1
    sub.save()
    WebhookAudit.objects.create(subscription=sub, actor=actor, action=action)
    return raw


@transaction.atomic
def test_event(subscription, actor):
    require_manager(actor)
    sub = WebhookSubscription.objects.select_for_update().get(pk=subscription.pk, enabled=True, archived=False)
    event = WebhookEvent.objects.create(product_id=sub.product_id, event_type="webhook.test", payload={"attributes": {}, "project": {"id": sub.product_id}}, subscribers={str(sub.pk): sub.revision})
    WebhookAudit.objects.create(subscription=sub, actor=actor, action="test")
    return event


@transaction.atomic
def replay_delivery(delivery, actor):
    require_manager(actor)
    sub = WebhookSubscription.objects.select_for_update().get(pk=delivery.subscription_id)
    row = WebhookDelivery.objects.select_for_update().get(pk=delivery.pk)
    if row.state not in {WebhookDelivery.State.DEAD, WebhookDelivery.State.SUCCEEDED, WebhookDelivery.State.CANCELLED}:
        msg = "Only terminal deliveries can be replayed."
        raise ValidationError(msg)
    if not sub.enabled or sub.archived:
        msg = "Enable the subscription before replay."
        raise ValidationError(msg)
    # Stable event/delivery IDs; history is retained and attempt numbering never resets.
    row.dispatch_until = None
    row.cycle_attempts = 0
    row.revision = sub.revision
    row.state = WebhookDelivery.State.PENDING
    row.next_attempt_at = timezone.now()
    row.last_error = ""
    row.save(update_fields=["revision", "cycle_attempts", "state", "next_attempt_at", "last_error", "dispatch_until"])
    WebhookAudit.objects.create(subscription=sub, actor=actor, action="replay")


def wire_payload(event):
    payload = {**event.payload, "event_id": str(event.pk), "event_type": event.event_type, "event_version": "1", "occurred_at": event.occurred_at.isoformat()}
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    if len(body) > settings.ASPM_WEBHOOK_MAX_PAYLOAD_BYTES:
        msg = "payload_too_large"
        raise ValidationError(msg)
    return body
