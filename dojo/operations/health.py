"""Small unauthenticated probes; responses never reveal dependency credentials."""
import copy

import psycopg
import redis
from django.conf import settings
from django.db import connections
from django.http import JsonResponse


def database_ready():
    params = copy.deepcopy(connections["default"].get_connection_params())
    params.update(connect_timeout=1, options="-c statement_timeout=1000 -c lock_timeout=1000")
    with psycopg.connect(**params) as db, db.cursor() as cursor:
        cursor.execute("SELECT 1")
        return cursor.fetchone() == (1,)


def redis_ready(url):
    try:
        client = redis.Redis.from_url(url, socket_connect_timeout=0.5, socket_timeout=0.5, retry=redis.retry.Retry(redis.backoff.NoBackoff(), 0))
    except ValueError:
        return False
    with client:
        return client.ping()


def probe(kind):
    if kind != "ready":
        return JsonResponse({"status": "ok", "probe": kind})
    try:
        ready = database_ready() and redis_ready(settings.CELERY_BROKER_URL)
        cache_url = settings.CACHES["default"].get("LOCATION")
        if isinstance(cache_url, str) and cache_url.startswith(("redis://", "rediss://")):
            ready = ready and redis_ready(cache_url)
        return JsonResponse({"status": "ok" if ready else "unavailable"}, status=200 if ready else 503)
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
