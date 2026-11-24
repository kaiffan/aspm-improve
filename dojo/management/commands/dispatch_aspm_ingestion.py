from django.core.management.base import BaseCommand

from dojo.aspm_ingestion.tasks import dispatch_jobs


class Command(BaseCommand):
    help = "Recover pending ASPM outbox jobs; normally Celery beat invokes this every 30 seconds."

    def handle(self, *args, **options):
        dispatch_jobs()
