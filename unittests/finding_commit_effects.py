"""
Simulate request commit effects in rollback-only Django TestCase unit tests.

These tests assert synchronous integration responses/VCR traffic. Their artificial
outer transaction never commits. Mock only the Finding effect registration, leaving
all persistence, model signals and other on_commit callbacks intact. The committed
connection oracles in test_finding_write_concurrency validate actual row unlocks;
they must never use this helper.
"""
from functools import wraps
from unittest.mock import patch


def eager_finding_commit_effects(cls):
    setup = cls.setUp

    @wraps(setup)
    def set_up(self):
        effect = patch("dojo.finding.write_effects.on_commit", side_effect=lambda callback, **_kwargs: callback())
        effect.start()
        self.addCleanup(effect.stop)
        setup(self)

    cls.setUp = set_up
    return cls
