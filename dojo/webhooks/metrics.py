from prometheus_client import Counter, Gauge, Histogram

from dojo.aspm_observability.metrics import ENABLED

ATTEMPTS = Counter("aspm_webhook_delivery_attempts_total", "Webhook HTTP attempts by bounded outcome", ["outcome"])
DURATION = Histogram("aspm_webhook_delivery_duration_seconds", "Webhook HTTP attempt duration", buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60))
EXPANDED = Counter("aspm_webhook_events_expanded_total", "Durable events expanded by this process")
PENDING = Gauge("aspm_webhook_pending_deliveries", "Pending, retry and in-flight deliveries at last dispatch")
OLDEST = Gauge("aspm_webhook_oldest_pending_seconds", "Age of oldest pending delivery at last dispatch")


class DurableOutboxCollector:

    """Database-authoritative queue gauges, visible from web replicas after worker replacement."""

    def describe(self):
        return []

    def collect(self):
        from django.conf import settings  # noqa: PLC0415 -- no app loading or DB reads at registration
        from django.db import connection, transaction  # noqa: PLC0415
        from django.utils import timezone  # noqa: PLC0415
        from prometheus_client.core import GaugeMetricFamily  # noqa: PLC0415

        if not settings.ASPM_WEBHOOKS_ENABLED:
            return
        available = GaugeMetricFamily("aspm_outbox_metrics_available", "Whether bounded operational SQL succeeded")
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = '1000ms'")
                cursor.execute("SELECT count(*) FILTER (WHERE state IN ('PENDING','RETRY','IN_FLIGHT')), min(created_at) FILTER (WHERE state IN ('PENDING','RETRY','IN_FLIGHT')), count(*) FILTER (WHERE state='DEAD') FROM dojo_webhookdelivery WHERE state IN ('PENDING','RETRY','IN_FLIGHT','DEAD')")
                pending, oldest, dead = cursor.fetchone()
                cursor.execute("SELECT count(*) FROM dojo_webhookevent WHERE expanded=false")
                events = cursor.fetchone()[0]
                cursor.execute("SELECT count(*) FROM dojo_ingestionjob")
                jobs = cursor.fetchone()[0]
            for name, help_text, value in (
                ("aspm_webhook_outbox_pending", "Durable active webhook deliveries", pending),
                ("aspm_webhook_outbox_oldest_seconds", "Age of oldest durable active delivery", max(0, (timezone.now() - oldest).total_seconds()) if oldest else 0),
                ("aspm_webhook_outbox_dead", "Dead-letter deliveries requiring review", dead),
                ("aspm_webhook_outbox_unexpanded", "Durable events awaiting fanout", events),
                ("aspm_ingestion_outbox_pending", "Scan/report jobs awaiting durable completion", jobs),
            ):
                metric = GaugeMetricFamily(name, help_text)
                metric.add_metric([], value)
                yield metric
            available.add_metric([], 1)
        except Exception:
            available.add_metric([], 0)
        yield available


def register_outbox_collector():
    from prometheus_client import REGISTRY  # noqa: PLC0415 -- explicit registry setup after models load

    if not ENABLED:
        REGISTRY.register(DurableOutboxCollector())
