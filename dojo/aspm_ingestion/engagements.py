from datetime import timedelta

from django.conf import settings
from django.db.models import F, Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from dojo.aspm_access.permissions import has_capability
from dojo.aspm_ingestion.models import EngagementPolicy, EngagementStrategy, ManagedEngagement
from dojo.engagement.models import Engagement
from dojo.scm.models import Repository


def can_manage_engagement_policy(user):
    return has_capability(user, "dojo.manage_engagement_policy")


def _policy(repository):
    return (
        EngagementPolicy.objects.filter(product_id=repository.product_id)
        .filter(Q(repository=repository) | Q(repository__isnull=True))
        .order_by(F("repository_id").desc(nulls_last=True))
        .values_list("strategy", flat=True).first()
        or settings.ASPM_DEFAULT_ENGAGEMENT_POLICY
    )


def _explicit_engagement(token, commit, pk):
    if "engagement:select" not in token.scopes:
        msg = "This token cannot select an Engagement."
        raise PermissionDenied(msg)
    engagement = (
        Engagement.objects.select_for_update(no_key=True)
        .filter(pk=pk, product_id=token.product_id, active=True, archived_at__isnull=True)
        .filter(Q(commit_id=commit.pk) | Q(commit__isnull=True))
        .first()
    )
    if engagement is not None:
        repository = commit.repository
        binding = ManagedEngagement.objects.filter(engagement=engagement).first()
        if binding:
            if binding.repository_id == repository.pk and binding.archived_at is None:
                return engagement
        elif (
            engagement.commit_id or engagement.source_code_management_uri == repository.url
            or (not token.repository_id and not engagement.source_code_management_uri)
        ):
            return engagement
    msg = "Engagement is outside the permitted scope or unavailable."
    raise PermissionDenied(msg)


def resolve_engagement(token, commit, metadata):
    repository = commit.repository
    if pk := metadata.get("engagement_id"):
        return _explicit_engagement(token, commit, pk)

    strategy = _policy(repository)
    if strategy == EngagementStrategy.DEFAULT:
        return None
    if strategy == EngagementStrategy.EXPLICIT:
        raise ValidationError({"engagement_id": "This policy requires an authorized Engagement ID."})

    field = {EngagementStrategy.BRANCH: "branch", EngagementStrategy.ENVIRONMENT: "environment"}.get(strategy)
    scope = metadata.get(field, "") if field else ""
    if field and not scope:
        raise ValidationError({field: "Required by the Engagement policy."})

    # The commit lock serializes one commit. A repository row also serializes the
    # first assignment for this scope across different commits, before any parsing.
    Repository.objects.select_for_update(no_key=True).get(pk=repository.pk)
    binding = ManagedEngagement.objects.filter(
        repository=repository, strategy=strategy, scope=scope, archived_at__isnull=True,
        engagement__active=True, engagement__archived_at__isnull=True,
    ).select_related("engagement").first()
    if binding:
        return binding.engagement

    today = timezone.localdate()
    # Legacy UI may close an Engagement. Retire its binding before creating a successor.
    ManagedEngagement.objects.filter(
        repository=repository, strategy=strategy, scope=scope, archived_at__isnull=True,
    ).update(archived_at=timezone.now())
    label = f"ASPM repository {repository.pk}"
    if field:
        label = f"{label} / {field}: {scope}"
    engagement = Engagement.objects.create(
        product_id=repository.product_id, name=label, engagement_type="CI/CD",
        target_start=today, target_end=today + timedelta(days=365), status="In Progress",
        source_code_management_uri=repository.url,
        branch_tag=scope if strategy == EngagementStrategy.BRANCH else None,
    )
    ManagedEngagement.objects.create(repository=repository, strategy=strategy, scope=scope, engagement=engagement)
    return engagement
