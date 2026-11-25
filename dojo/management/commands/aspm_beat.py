import signal
import subprocess
import sys
import time

from django.core.management import BaseCommand, CommandError
from django.db import connection

LOCK_ID = 62721683045711


class Command(BaseCommand):
    help = "Run one Celery scheduler per database, fenced by a session advisory lock. Requires session pooling."

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s)", [LOCK_ID])
            if not cursor.fetchone()[0]:
                msg = "Another ASPM scheduler owns this database."
                raise CommandError(msg)
        child = subprocess.Popen([sys.executable, "-m", "celery", "--app=dojo", "beat", "--pidfile=/tmp/aspm-beat.pid", "--schedule=/tmp/aspm-beat-schedule"])
        stopping = False

        def stop(signum, frame):
            nonlocal stopping
            stopping = True
            child.send_signal(signum)

        prior = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT)}
        try:
            while child.poll() is None:
                time.sleep(1)
                if stopping:
                    continue
                # Failure of the lock's connection must stop this scheduler, not reconnect it.
                try:
                    connection.connection.execute("SELECT 1")
                except Exception as error:
                    child.terminate()
                    msg = "Scheduler fencing connection was lost."
                    raise CommandError(msg) from error
            if child.returncode and not stopping:
                msg = "Celery scheduler exited unsuccessfully."
                raise CommandError(msg)
        finally:
            if child.poll() is None:
                child.terminate()
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
            for sig, handler in prior.items():
                signal.signal(sig, handler)
            connection.close()
