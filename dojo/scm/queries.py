"""Product-scoped queries for SCM objects and commit comparisons."""

from django.db.models import Case, CharField, Exists, Min, OuterRef, Q, Value, When
from django.db.models.functions import Coalesce, Concat

from dojo.finding.queries import get_authorized_findings
from dojo.product.queries import get_authorized_products
from dojo.scm.models import Commit, Repository


def authorized_repositories(user):
    return Repository.objects.filter(product__in=get_authorized_products("view", user=user)).select_related("product")


def authorized_commits(user):
    return Commit.objects.filter(repository__product__in=get_authorized_products("view", user=user)).select_related("repository__product")


def compare_findings(user, base, target, category, *, after, page_size):
    """Return representative findings for one comparison category and a continuation ID."""
    hash_present = Q(hash_code__isnull=False) & ~Q(hash_code="")
    uid_present = Q(unique_id_from_tool__isnull=False) & ~Q(unique_id_from_tool="")
    visible = get_authorized_findings("view", user=user).filter(
        hash_present | uid_present,
        test__engagement__product_id=target.repository.product_id,
        test__engagement__commit_id__in=(base.pk, target.pk),
        is_mitigated=False,
    ).annotate(
        comparison_service=Coalesce("service", Value("")),
        comparison_fingerprint=Case(
            When(hash_present, then=Concat(Value("hash:"), "hash_code")),
            default=Concat(Value("uid:"), "unique_id_from_tool"),
            output_field=CharField(),
        ),
    )
    before = visible.filter(test__engagement__commit_id=base.pk)
    after_commit = visible.filter(test__engagement__commit_id=target.pk)
    source, other = (before, after_commit) if category == "fixed" else (after_commit, before)
    corresponding = Exists(other.filter(
        test__test_type_id=OuterRef("test__test_type_id"),
        comparison_service=OuterRef("comparison_service"),
        comparison_fingerprint=OuterRef("comparison_fingerprint"),
    ))
    matching = source.filter(corresponding if category == "unchanged" else ~corresponding)
    representatives = matching.values("test__test_type_id", "comparison_service", "comparison_fingerprint").annotate(
        representative=Min("pk"),
    ).filter(representative__gt=after).order_by("representative")
    ids = list(representatives.values_list("representative", flat=True)[:page_size + 1])
    rows = visible.filter(pk__in=ids[:page_size]).only("title", "severity").order_by("pk")
    return rows, ids[page_size - 1] if len(ids) > page_size else None
