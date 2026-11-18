"""Product metric counts and complete chart buckets without retaining Finding rows."""
import calendar
from datetime import UTC, datetime

from django.db.models import Count, OuterRef, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from dojo.models import Finding, Test
from dojo.query_utils import build_count_subquery
from dojo.utils import get_zero_severity_level


def _counts(queryset):
    counts = get_zero_severity_level()
    total = 0
    for row in queryset.order_by().values("severity").annotate(n=Count("pk")).iterator(chunk_size=1000):
        total += row["n"]
        if row["severity"] in counts:
            counts[row["severity"]] += row["n"]
    return total, counts


def product_metric_context(filters, product):
    """Aggregate in PostgreSQL; Python memory grows with chart dates, not finding count."""
    context = {}
    for source, target in (("verified", "verified"), ("inactive", "inactive"),
                           ("false_positive", "false_positive"), ("out_of_scope", "out_of_scope"),
                           ("new_verified", "new"), ("all", "all"), ("open", "open"),
                           ("closed", "closed"), ("accepted", "accepted")):
        total, counts = _counts(filters[source])
        context[target + "_objs"] = total
        context[target + "_objs_by_severity"] = counts

    open_close, severity_weekly, by_severity, ages = {}, {}, {s: {} for s in ("Critical", "High", "Medium")}, {}

    def week_bucket(day):
        monday = datetime.fromisocalendar(*day.isocalendar()[:2], 1)
        return calendar.timegm(monday.timetuple()) * 1000, monday.strftime("<span class='small'>%m/%d<br/>%Y</span>")

    def add(day, category, count):
        stamp, label = week_bucket(day)
        bucket = open_close.setdefault(stamp, {"closed": 0, "open": 0, "accepted": 0, "week": label})
        bucket[category] += count
        return stamp, label

    today = timezone.now().date()
    for row in filters["open"].order_by().values("date", "severity").annotate(n=Count("pk")).iterator(chunk_size=1000):
        stamp, label = add(row["date"], "open", row["n"])
        bucket = severity_weekly.setdefault(stamp, {**get_zero_severity_level(), "week": label})
        bucket[row["severity"]] = bucket.get(row["severity"], 0) + row["n"]
        for severity, series in by_severity.items():
            item = series.setdefault(stamp, {"count": 0, "week": label})
            if severity == row["severity"]:
                item["count"] += row["n"]
        age = max(0, (today - row["date"]).days)
        ages[age] = ages.get(age, 0) + row["n"]

    # The legacy view classifies open before closed. Keep that precedence even for
    # inconsistent endpoint status rows. A datetime returned by PostgreSQL is UTC;
    # use its UTC date just as the original datetime.date() did, including at midnight.
    closed = filters["closed"]
    if closed.model._meta.model_name == "finding":
        # All discovery dates fall within the min/max dates of this same filtered
        # scope. Open membership therefore means active=True. Avoid a large NOT IN
        # subquery, which can become a repeated materialized scan on large products.
        closed = closed.filter(active=False).annotate(
            metric_day=Coalesce(TruncDate("mitigated", tzinfo=UTC), "date"),
        )
    else:
        # Endpoint_Status.mitigated is boolean; its discovery date is the fallback.
        closed = closed.annotate(metric_day=Coalesce(TruncDate("mitigated_time", tzinfo=UTC), "date"))
    for row in closed.order_by().values("metric_day").annotate(n=Count("pk")).iterator(chunk_size=1000):
        add(row["metric_day"], "closed", row["n"])
    for row in filters["accepted"].order_by().values("date").annotate(n=Count("pk")).iterator(chunk_size=1000):
        add(row["date"], "accepted", row["n"])

    context.update({
        "open_close_weekly": dict(sorted(open_close.items())),
        "severity_weekly": dict(sorted(severity_weekly.items())),
        "open_objs_by_age": ages,
        **{severity.lower() + "_weekly": dict(sorted(series.items())) for severity, series in by_severity.items()},
    })
    for source, target in (("open_vulns", "open_vulnerabilities"), ("all_vulns", "all_vulnerabilities")):
        rows = [["CWE-" + str(row["cwe"]), row["count"]] for row in filters[source].values("cwe", "count").iterator(chunk_size=1000)]
        context[target] = rows
        context[target + "_count"] = len(rows)

    # The old prefetch of finding_set loaded every Finding even though only this
    # aggregate was consumed. Count by test type in SQL, retaining empty test types.
    verified = build_count_subquery(Finding.objects.filter(test=OuterRef("pk"), verified=True), "test_id")
    tests = Test.objects.filter(engagement__product=product).order_by().values("test_type__name").annotate(
        total=Sum(Coalesce(verified, Value(0))),
    )
    context["test_data"] = {row["test_type__name"]: row["total"] for row in tests.iterator(chunk_size=1000)}
    return context
