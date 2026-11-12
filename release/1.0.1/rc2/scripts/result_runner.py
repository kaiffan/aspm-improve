"""Record real unittest outcomes without counting subtests as separate methods."""
import json
import unittest
from pathlib import Path
from django.test.runner import DiscoverRunner


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.success_ids = []

    def addSuccess(self, test):
        self.success_ids.append(test.id())
        super().addSuccess(test)


class RecordRunner(DiscoverRunner):
    def get_resultclass(self):
        return RecordedResult

    def run_suite(self, suite, **kwargs):
        result = super().run_suite(suite, **kwargs)
        data = {
            'tests_run': result.testsRun,
            'passed': len(result.success_ids),
            'assertion_failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped),
            'expected_failures': len(result.expectedFailures),
            'unexpected_successes': len(result.unexpectedSuccesses),
            'failure_details': [{'test': t.id(), 'last_line': message.strip().splitlines()[-1]} for t, message in result.failures],
            'error_details': [{'test': t.id(), 'last_line': message.strip().splitlines()[-1]} for t, message in result.errors],
            'skip_details': [{'test': t.id(), 'reason': reason} for t, reason in result.skipped],
            'passed_ids': result.success_ids,
        }
        Path('/tmp/rc2-test-summary.json').write_text(json.dumps(data, indent=2)+'\n')
        return result
