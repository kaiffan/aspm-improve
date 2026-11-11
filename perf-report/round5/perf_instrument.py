"""Identical diagnostic middleware on all candidates. Never records SQL bindings."""
import hashlib
import json
import os
import re
import time

from django.db import connection


class SQLMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        queries = []
        count = 0
        elapsed = 0.0
        logging = os.environ.get("DD_R5_SQL_LOG") == "1"

        def measure(execute, sql, params, many, context):
            nonlocal count, elapsed
            start = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                duration = (time.perf_counter() - start) * 1000
                count += 1
                elapsed += duration
                if logging:
                    # SQL argument only, never cursor.query (which interpolates secrets).
                    shape = re.sub(r"'(?:[^']|'')*'", "'<redacted>'", str(sql))
                    shape = re.sub(r"(?:%s, ){2,}%s", "%s, ...", shape)
                    queries.append({"id": hashlib.sha256(shape.encode()).hexdigest()[:16],
                                    "sql": shape, "ms": round(duration, 3),
                                    "rows": context["cursor"].rowcount})

        with connection.execute_wrapper(measure):
            response = self.get_response(request)
        response["X-Perf-SQL-Count"] = str(count)
        response["X-Perf-SQL-Ms"] = f"{elapsed:.3f}"
        if logging:
            line = json.dumps({"path": request.path, "queries": queries}) + "\n"
            fd = os.open("/tmp/r5-sql.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            try:
                os.write(fd, line.encode())
            finally:
                os.close(fd)
        return response
