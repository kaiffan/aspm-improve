from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import Count, F, Q, Value

try:
    from dojo.authorization.query_filters import get_auth_filter
except ImportError:
    def get_auth_filter(key): return None

from dojo.models import (
    App_Analysis,
    DojoMeta,
    Engagement_Presets,
    Languages,
    Product,
    Product_API_Scan_Configuration,
)
from dojo.query_utils import TestIdInArray
from dojo.request_cache import cache_for_request_or_task


# Cached: all parameters are hashable, no dynamic queryset filtering
@cache_for_request_or_task
def get_authorized_products(permission, user=None):
    impl = get_auth_filter("product.get_authorized_products")
    if impl:
        return impl(permission, user=user)
    return Product.objects.all().order_by("name")


# Cached: all parameters are hashable, no dynamic queryset filtering
@cache_for_request_or_task
def get_authorized_app_analysis(permission):
    impl = get_auth_filter("product.get_authorized_app_analysis")
    if impl:
        return impl(permission)
    return App_Analysis.objects.all().order_by("id")


# Cached: all parameters are hashable, no dynamic queryset filtering
@cache_for_request_or_task
def get_authorized_dojo_meta(permission):
    impl = get_auth_filter("product.get_authorized_dojo_meta")
    if impl:
        return impl(permission)
    return DojoMeta.objects.all().order_by("id")


# Cached: all parameters are hashable, no dynamic queryset filtering
@cache_for_request_or_task
def get_authorized_languages(permission):
    impl = get_auth_filter("product.get_authorized_languages")
    if impl:
        return impl(permission)
    return Languages.objects.all().order_by("id")


# Cached: all parameters are hashable, no dynamic queryset filtering
@cache_for_request_or_task
def get_authorized_engagement_presets(permission):
    impl = get_auth_filter("product.get_authorized_engagement_presets")
    if impl:
        return impl(permission)
    return Engagement_Presets.objects.all().order_by("id")


# Cached: all parameters are hashable, no dynamic queryset filtering
@cache_for_request_or_task
def get_authorized_product_api_scan_configurations(permission):
    impl = get_auth_filter("product.get_authorized_product_api_scan_configurations")
    if impl:
        return impl(permission)
    return Product_API_Scan_Configuration.objects.all().order_by("id")


def get_active_findings_by_product(product_ids):
    """
    Group active findings for an already authorized Product page.

    For one Product, a constant grouping key avoids joining every Finding back
    to Test. The explicit Test-ID array also avoids a nested loop that visits
    the same heap pages once for each Test on a large Product.
    """
    from dojo.models import Finding, Test  # noqa: PLC0415 -- avoids circular dependency

    findings = Finding.objects.filter(active=True).order_by()
    if len(product_ids) == 1:
        tests = Test.unfiltered.filter(engagement__product_id=product_ids[0]).order_by().values("pk")
        return findings.filter(TestIdInArray(F("test_id"), ArraySubquery(tests))).annotate(
            _product_id=Value(product_ids[0]),
        ).values("_product_id")
    return findings.filter(test__engagement__product_id__in=product_ids).annotate(
        _product_id=F("test__engagement__product_id"),
    ).values("_product_id")


def get_active_finding_counts_by_product(product_ids):
    """Count only findings for the already authorized products on the page."""
    rows = get_active_findings_by_product(product_ids).annotate(
        active=Count("pk"), verified=Count("pk", filter=Q(verified=True)),
    )
    return {row["_product_id"]: (row["active"], row["verified"]) for row in rows if row["active"]}
