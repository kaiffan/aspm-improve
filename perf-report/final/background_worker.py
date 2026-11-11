import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dojo.settings.settings')
import perf_bg_instrument  # noqa: E402,F401 -- benchmark-only Celery signals
from dojo.celery import app  # noqa: E402

app.worker_main(['worker', '--concurrency=1', '--pool=prefork', '--prefetch-multiplier=1', '--soft-time-limit=90', '--time-limit=120',
                 '--loglevel=WARNING', '--without-gossip', '--without-mingle'])
