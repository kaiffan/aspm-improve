import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class WebhookSubscription(models.Model):
    product = models.ForeignKey("dojo.Product", on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    endpoint = models.URLField(max_length=1000)
    enabled = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
    events = models.JSONField(default=list)
    filters = models.JSONField(default=dict, blank=True)
    encrypted_secret = models.TextField()
    revision = models.PositiveIntegerField(default=1)
    timeout_seconds = models.PositiveSmallIntegerField(default=5)
    max_attempts = models.PositiveSmallIntegerField(default=6)
    rate_per_minute = models.PositiveSmallIntegerField(default=60)
    next_send_at = models.DateTimeField(default=timezone.now)
    last_success_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("manage_outbound_webhooks", "Manage ASPM outbound webhooks across platform products")]
        indexes = [models.Index(fields=("product", "enabled"), name="aspm_hook_product_enabled")]


class WebhookEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey("dojo.Product", on_delete=models.PROTECT)
    event_type = models.CharField(max_length=64)
    occurred_at = models.DateTimeField(default=timezone.now)
    payload = models.JSONField()
    # Subscription revisions at the business transaction's time, never retroactive subscriptions.
    subscribers = models.JSONField(default=dict)
    expanded = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=("expanded", "occurred_at"), name="aspm_hook_event_pending")]


class WebhookDelivery(models.Model):
    class State(models.TextChoices):
        PENDING = "PENDING"
        IN_FLIGHT = "IN_FLIGHT"
        RETRY = "RETRY"
        SUCCEEDED = "SUCCEEDED"
        DEAD = "DEAD"
        CANCELLED = "CANCELLED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(WebhookEvent, on_delete=models.PROTECT)
    subscription = models.ForeignKey(WebhookSubscription, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    state = models.CharField(max_length=16, choices=State, default=State.PENDING)
    attempts = models.PositiveIntegerField(default=0)
    cycle_attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    dispatch_until = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("event", "subscription"), name="aspm_hook_delivery_unique")]
        indexes = [models.Index(fields=("state", "next_attempt_at"), name="aspm_hook_delivery_due")]


class WebhookAttempt(models.Model):
    delivery = models.ForeignKey(WebhookDelivery, related_name="history", on_delete=models.PROTECT)
    number = models.PositiveIntegerField()
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    error_code = models.CharField(max_length=64, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("delivery", "number"), name="aspm_hook_attempt_unique")]


class WebhookAudit(models.Model):
    subscription = models.ForeignKey(WebhookSubscription, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=40)
    occurred_at = models.DateTimeField(auto_now_add=True)


from dojo.webhooks.metrics import register_outbox_collector  # noqa: E402 -- models are ready

register_outbox_collector()
