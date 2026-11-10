from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from dojo.authorization.authorization import user_has_permission
from dojo.importers.auto_create_context import AutoCreateContextManager
from dojo.location.models import Location, LocationProductReference
from dojo.models import Engagement, Product, Test
from dojo.scm.identity_v1 import repository_provider
from dojo.scm.models import Commit, Repository, normalize_repository_url, normalize_sha


@dataclass(frozen=True)
class ScmScanTarget:
    product: Product
    url: str
    sha: str
    engagement: Engagement | None
    test: Test | None
    explicit: bool


def resolve_scm_scan(data, manager, user, *, reimport):
    """Resolve a scan destination and check import permission without writing any rows."""
    if not settings.ASPM_SCM_HIERARCHY:
        raise ValidationError({"repository_url": "SCM hierarchy is disabled."})
    url = normalize_repository_url(data.get("repository_url"))
    sha = normalize_sha(data.get("commit_hash"))
    if (legacy_url := data.get("source_code_management_uri")) and normalize_repository_url(legacy_url) != url:
        raise ValidationError({"source_code_management_uri": "The URL differs from repository_url."})

    target_key = "test" if reimport else "engagement"
    identifiers = {key: data[key] for key in (target_key, "product_name", "product_type_name", "engagement_name") if key in data}
    manager.process_import_meta_data_from_dict(identifiers)
    test_id = identifiers.get("test_id") if reimport else None
    engagement_id = identifiers.get("engagement_id") if not reimport else None
    test = None
    engagement = None
    if test_id:
        test = manager.get_target_test_if_exists(test_id=test_id)
        if test is None:
            raise ValidationError({"test": "Test does not exist."})
        engagement = test.engagement
    elif engagement_id:
        engagement = manager.get_target_engagement_if_exists(engagement_id=engagement_id)
        if engagement is None:
            raise ValidationError({"engagement": "Engagement does not exist."})

    product_name = identifiers.get("product_name")
    if engagement is not None:
        product = engagement.product
    else:
        product = manager.get_target_product_if_exists(product_name=product_name)
    if product is None:
        raise ValidationError({"product_name": "Select an existing product for the SCM scan."})
    if not user_has_permission(user, test or engagement or product, "import"):
        raise PermissionDenied

    if product_name and product.name != product_name:
        raise ValidationError({"product_name": "The name differs from the target product."})
    if (type_name := identifiers.get("product_type_name")) and product.prod_type.name != type_name:
        raise ValidationError({"product_type_name": "The name differs from the target product type."})
    engagement_name = identifiers.get("engagement_name")
    if engagement is not None:
        if engagement_name and engagement_name != engagement.name:
            raise ValidationError({"engagement_name": "The name differs from the target engagement."})
        check_engagement_commit(engagement, url, sha)
        check_test_commit(test, sha)
        if test is not None and test.scan_type and test.scan_type != data.get("scan_type"):
            raise ValidationError({"scan_type": "The scan type differs from the target test."})
        if test is not None and (title := data.get("test_title")) and test.title != title:
            raise ValidationError({"test_title": "The title differs from the target test."})
    else:
        engagements = Engagement.objects.filter(
            product=product, commit__repository__product=product, commit__repository__url=url, commit__sha=sha,
        )
        if engagement_name:
            engagements = engagements.filter(name=engagement_name)
        engagement = engagements.order_by("pk").first()
        if reimport and engagement is not None:
            test = manager.get_target_test_if_exists(engagement=engagement, scan_type=data.get("scan_type"), test_title=data.get("test_title"))
        if engagement is not None and not user_has_permission(user, test or engagement, "import"):
            raise PermissionDenied

    if (engagement is None or engagement.commit_id is None) and not user_has_permission(user, product, "add"):
        raise PermissionDenied
    return ScmScanTarget(product, url, sha, engagement, test, bool(test_id or engagement_id))


def check_engagement_commit(engagement, url, sha):
    if engagement.commit_id is not None:
        commit = engagement.commit
        if commit.repository.product_id != engagement.product_id or commit.repository.url != url or commit.sha != sha:
            raise ValidationError({"commit_hash": "The engagement belongs to a different SCM commit."})
        return
    recorded_url = (engagement.source_code_management_uri or "").strip()
    if recorded_url and normalize_repository_url(recorded_url) != url:
        raise ValidationError({"repository_url": "The target engagement records a different repository."})
    recorded_sha = (engagement.commit_hash or "").strip()
    if recorded_sha and normalize_sha(recorded_sha) != sha:
        raise ValidationError({"commit_hash": "The target engagement records a different commit."})


def check_test_commit(test, sha):
    if test is not None and (recorded_sha := (test.commit_hash or "").strip()) and normalize_sha(recorded_sha) != sha:
        raise ValidationError({"commit_hash": "The target test records a different commit."})


def validate_scan_related_objects(data, product):
    if (configuration := data.get("api_scan_configuration")) and configuration.product_id != product.pk:
        raise ValidationError({"api_scan_configuration": "Select a configuration from the target product."})
    if endpoint := data.get("endpoint_to_add"):
        if isinstance(endpoint, Location):
            matches = LocationProductReference.objects.filter(product=product, location=endpoint).exists()
        else:
            matches = endpoint.product_id == product.pk
        if not matches:
            raise ValidationError({"endpoint_to_add": "Select a location from the target product."})


@transaction.atomic
def materialize_scm_scan(target, data, user, *, reimport):
    repository, _ = Repository.objects.get_or_create(
        product=target.product, url=target.url, defaults={"provider": repository_provider(target.url)},
    )
    branch = data.get("branch_tag", "")
    # Commit identity is unique. Its row lock serializes automatic engagement creation for this commit.
    commit, _ = Commit.objects.select_for_update().get_or_create(
        repository=repository, sha=target.sha, defaults={"branch": branch},
    )
    test = None
    if target.explicit:
        engagement = Engagement.objects.select_for_update().filter(pk=target.engagement.pk, product=target.product).first()
        if engagement is None:
            raise ValidationError({"engagement": "The target engagement is no longer available."})
        check_engagement_commit(engagement, target.url, target.sha)
        if target.test is not None:
            test = Test.objects.select_for_update().filter(pk=target.test.pk, engagement=engagement).first()
            if test is None:
                raise ValidationError({"test": "The target test is no longer available."})
    else:
        engagements = Engagement.objects.select_for_update().filter(product=target.product, commit=commit)
        if engagement_name := data.get("engagement_name"):
            engagements = engagements.filter(name=engagement_name)
        engagement = engagements.order_by("pk").first()
        if reimport and engagement is not None:
            test = AutoCreateContextManager().get_target_test_if_exists(
                engagement=engagement, scan_type=data.get("scan_type"), test_title=data.get("test_title"),
            )

    if reimport and test is None and not data.get("auto_create_context"):
        raise ValidationError({"test": "No matching test exists for this commit. Enable auto_create_context to create one."})
    if not user_has_permission(user, test or engagement or target.product, "import"):
        raise PermissionDenied
    check_test_commit(test, target.sha)
    if engagement is None:
        if not user_has_permission(user, target.product, "add"):
            raise PermissionDenied
        today = timezone.localdate()
        target_end = data.get("target_end")
        if target_end is None or target_end < today:
            target_end = today + timedelta(days=365)
        repository_name = urlsplit(target.url).path.rsplit("/", 1)[-1]
        engagement = Engagement.objects.create(
            product=target.product, commit=commit, name=data.get("engagement_name") or f"{repository_name[:250]} @ {target.sha[:12]}",
            lead_id=user.pk, engagement_type="CI/CD", status="In Progress", target_start=today, target_end=target_end,
            source_code_management_uri=target.url, commit_hash=target.sha, branch_tag=branch,
            deduplication_on_engagement=data.get("deduplication_on_engagement", False),
        )
    elif engagement.commit_id is None:
        if not user_has_permission(user, target.product, "add"):
            raise PermissionDenied
        engagement.commit = commit
        if not (engagement.source_code_management_uri or "").strip():
            engagement.source_code_management_uri = target.url
        if not (engagement.commit_hash or "").strip():
            engagement.commit_hash = target.sha
        engagement.save(update_fields=["commit", "source_code_management_uri", "commit_hash"])
    return engagement, test
