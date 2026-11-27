"""Exercise the same multiprocess collector used by the Kubernetes sidecars."""
# ruff: noqa: INP001
import os
import subprocess
import sys
import tempfile
import unittest

from prometheus_client import CollectorRegistry, generate_latest, multiprocess
from prometheus_client.parser import text_string_to_metric_families


class MultiprocessTest(unittest.TestCase):
    def test_independent_processes_accumulate_and_startup_resets(self):
        with tempfile.TemporaryDirectory() as folder:
            env = os.environ | {"PROMETHEUS_MULTIPROC_DIR": folder, "DD_ASPM_OBSERVABILITY": "true"}
            action = """
from dojo.aspm_observability.metrics import SCAN_PHASE, scan_event
from dojo.webhooks.metrics import ATTEMPTS
import sys
for _ in range(int(sys.argv[1])):
    scan_event("Semgrep JSON Report", "completed")
    SCAN_PHASE.labels("semgrep", "parser").observe(0.2)
    ATTEMPTS.labels(outcome="success").inc()
"""
            children = [subprocess.Popen([sys.executable, "-c", action, str(count)], env=env) for count in (2, 3)]
            for child in children:
                self.assertEqual(child.wait(timeout=15), 0)
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry, path=folder)

            def metric_values():
                return {(sample.name, tuple(sorted(sample.labels.items()))): sample.value
                        for family in text_string_to_metric_families(generate_latest(registry).decode()) for sample in family.samples}

            values = metric_values()
            scan = ("aspm_scan_events_total", (("result", "completed"), ("scanner", "semgrep")))
            webhook = ("aspm_webhook_delivery_attempts_total", (("outcome", "success"),))
            parser = ("aspm_scan_phase_seconds_count", (("scanner", "semgrep"), ("stage", "parser")))
            self.assertEqual((values[scan], values[webhook], values[parser]), (5, 5, 5))
            subprocess.run([sys.executable, "-m", "dojo.aspm_observability.launch", sys.executable, "-c", action, "1"], env=env, check=True, timeout=15)
            values = metric_values()
            self.assertEqual((values[scan], values[webhook], values[parser]), (1, 1, 1))


if __name__ == "__main__":
    unittest.main()
