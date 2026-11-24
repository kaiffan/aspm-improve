import logging
from contextlib import contextmanager
from contextvars import ContextVar

_sensitive_import = ContextVar("aspm_sensitive_import", default=False)


class EvidenceLogFilter(logging.Filter):
    def filter(self, record):
        return not _sensitive_import.get() or record.name.startswith("dojo.aspm_ingestion")


_filter = EvidenceLogFilter()


@contextmanager
def private_import_logs():
    """Parser messages/SQL can contain report contents. Keep only safe ASPM operational records."""
    loggers = [logging.getLogger(), *[item for item in logging.Logger.manager.loggerDict.values() if isinstance(item, logging.Logger)]]
    for logger in loggers:
        for handler in logger.handlers:
            if _filter not in handler.filters:
                handler.addFilter(_filter)
    token = _sensitive_import.set(True)
    try:
        yield
    finally:
        _sensitive_import.reset(token)
