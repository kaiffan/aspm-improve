import importlib
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from celery import Celery

from unittests.dojo_test_case import DojoTestCase


class TestWSGITaskStartup(DojoTestCase):
    def test_wsgi_prepares_lazy_tasks_before_concurrent_requests(self):
        isolated = Celery("wsgi_startup_regression", set_as_current=False)
        barrier = Barrier(8)

        @isolated.task(bind=True, name="wsgi_startup.echo")
        def echo(task, value):
            barrier.wait(timeout=10)
            return task.request.args[0], value

        self.assertFalse(isolated.finalized)
        from dojo import wsgi  # noqa: PLC0415 -- test real WSGI initialization

        with patch("dojo.celery.app", isolated):
            importlib.reload(wsgi)
        self.assertTrue(isolated.finalized)
        task = isolated._tasks["wsgi_startup.echo"]
        self.assertIsNotNone(task.request_stack)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(task, range(8)))
        self.assertEqual(results, [(value, value) for value in range(8)])
        self.assertIsNone(task.request_stack.top)
        isolated.close()
