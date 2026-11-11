"""Benchmark-only middleware, mounted identically into every isolated build."""
from time import perf_counter

from django.db import connection


class SQLMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        count = 0
        elapsed = 0.0

        def measure(execute, sql, params, many, context):
            nonlocal count, elapsed
            start = perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                count += 1
                elapsed += (perf_counter() - start) * 1000

        with connection.execute_wrapper(measure):
            response = self.get_response(request)
        response['X-Perf-SQL-Count'] = str(count)
        response['X-Perf-SQL-Ms'] = f'{elapsed:.3f}'
        return response
