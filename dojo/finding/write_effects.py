"""Keep external integrations outside the short Finding database write phase."""

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps

from django.db.transaction import on_commit

_effects = ContextVar("finding_write_effects", default=None)


def after_finding_write(callback):
    pending = _effects.get()
    if pending is None:
        return callback()
    pending.append(callback)
    return None


def external_finding_effect(func):
    @wraps(func)
    def deferred(*args, **kwargs):
        return after_finding_write(lambda: func(*args, **kwargs))

    return deferred


@contextmanager
def finding_write_effects(*, using=None):
    """
    Enter before atomic(), so callbacks run after its commit and row unlock.

    Nested writes join their successful effects to the enclosing write phase.
    A failed phase discards its effects. If the caller owns a wider transaction,
    on_commit also respects that boundary rather than performing network I/O with
    its locks held. ContextVar stores callbacks, never serializes database writers.
    """
    parent = _effects.get()
    pending = []
    token = _effects.set(pending)
    try:
        yield
    except BaseException:
        _effects.reset(token)
        raise
    else:
        _effects.reset(token)
        if parent is not None:
            parent.extend(pending)
        elif pending:
            def run():
                for callback in pending:
                    callback()

            on_commit(run, using=using)
