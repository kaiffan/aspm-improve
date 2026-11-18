"""
Merge an existing Finding's local edits against its locked current row.

Model saves may receive instances loaded long before the write (import batches,
Celery, forms). A row lock taken without rebasing that state still loses updates.
Only the mutations since loading are carried onto the current row; model derivation
and signals then run normally while that row is locked. No parsing or external
post-processing belongs in this context.
"""
from contextlib import contextmanager

from django.db import router, transaction


def loaded_values(finding):
    return {
        field.attname: finding.__dict__[field.attname]
        for field in finding._meta.concrete_fields
        if field.attname in finding.__dict__
    }


def remember_loaded_values(finding):
    finding._loaded_finding_values = loaded_values(finding)


def remember_saved_values(finding):
    # A subsequent save inside this transaction must compare with the row just
    # written, while rollback must retain the caller's explicit intent for retry.
    remember_loaded_values(finding)
    assignments = getattr(finding, "_finding_assignments", {}).copy()

    def acknowledge():
        current = getattr(finding, "_finding_assignments", {})
        for name, version in assignments.items():
            if current.get(name) == version:
                current.pop(name, None)

    transaction.on_commit(acknowledge, using=finding._state.db)


@contextmanager
def merge_finding_write(finding, *, using=None, update_fields=None):
    if finding.pk is None or finding._state.adding:
        yield
        return
    db = using or router.db_for_write(type(finding), instance=finding)
    fields = [field for field in finding._meta.concrete_fields if not field.primary_key]
    before = getattr(finding, "_loaded_finding_values", {})
    assignments = getattr(finding, "_finding_assignments", {})
    if update_fields is None:
        edits = {
            field.attname: finding.__dict__[field.attname]
            for field in fields if field.attname in finding.__dict__
            and (field.attname in assignments or field.attname not in before or finding.__dict__[field.attname] != before[field.attname])
        }
    else:
        edits = {field.attname: getattr(finding, field.attname) for field in fields
                 if field.name in update_fields or field.attname in update_fields}
    loaded = {field.attname for field in fields if field.attname in finding.__dict__}
    with transaction.atomic(using=db, savepoint=False):
        # NO KEY UPDATE permits unrelated FK inserts and shares the existing
        # delete/dedup lock order. No joins means no accidentally locked Test/Product.
        current = type(finding).unfiltered.using(db).only("pk", *loaded).select_for_update(no_key=True).get(pk=finding.pk)
        was_rebasing = getattr(finding, "_finding_rebasing", False)
        finding._finding_rebasing = True
        try:
            for field in fields:
                if field.attname in current.__dict__:
                    setattr(finding, field.attname, current.__dict__[field.attname])
            for name, value in edits.items():
                setattr(finding, name, value)
            yield
        finally:
            finding._finding_rebasing = was_rebasing


def save_base_fields(finding):
    """Preserve base-save signals without re-running Finding post-processing."""
    from dojo.finding.models import Finding  # noqa: PLC0415 -- avoids model import cycle

    with merge_finding_write(finding):
        super(Finding, finding).save(skip_validation=True)
        remember_saved_values(finding)
