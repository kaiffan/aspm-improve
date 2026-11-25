import time

from django.core.management import BaseCommand, CommandError, call_command
from django.db import connection

LOCK_ID = 62721683045710


class Command(BaseCommand):
    help = "Run migrations under a PostgreSQL session lock; schema rollback is a separate operation."

    def add_arguments(self, parser):
        parser.add_argument("--lock-wait-seconds", type=int, default=120)

    def handle(self, *args, **options):
        deadline = time.monotonic() + options["lock_wait_seconds"]
        acquired = False
        try:
            while not acquired:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_try_advisory_lock(%s)", [LOCK_ID])
                    acquired = cursor.fetchone()[0]
                if not acquired:
                    if time.monotonic() >= deadline:
                        msg = "Another ASPM migration executor holds the schema lock."
                        raise CommandError(msg)
                    time.sleep(1)
            # Migration files 0307/0316 and all their dependencies remain authoritative.
            call_command("migrate", interactive=False, verbosity=options["verbosity"])
            call_command("migrate", check_unapplied=True, interactive=False, verbosity=0)
        finally:
            if acquired:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_unlock(%s)", [LOCK_ID])
