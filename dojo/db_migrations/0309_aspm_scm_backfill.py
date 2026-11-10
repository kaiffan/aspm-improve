"""Link unambiguous legacy Engagement SCM metadata in bounded batches."""

import logging
from collections import defaultdict
from functools import reduce
from operator import or_

from django.db import migrations, transaction
from django.db.models import Q

BATCH_SIZE = 500
logger = logging.getLogger(__name__)


def matching_pairs(queryset, owner_field, value_field, pairs):
    by_owner = defaultdict(list)
    for owner, value in pairs:
        by_owner[owner].append(value)
    predicates = (
        Q(**{owner_field: owner, f"{value_field}__in": values})
        for owner, values in by_owner.items()
    )
    return queryset.filter(reduce(or_, predicates))


def link_batch(engagements, repositories, commits, rows):
    from dojo.scm.identity_v1 import (  # noqa: PLC0415 -- frozen migration identity rules
        canonical_repository_url,
        canonical_sha,
        repository_provider,
    )

    identities = {}
    for engagement_id, product_id, raw_url, raw_sha in rows:
        try:
            url = canonical_repository_url(raw_url)
            sha = canonical_sha(raw_sha)
        except ValueError:
            continue
        identities[engagement_id] = (product_id, url, sha)

    if not identities:
        return 0

    repository_keys = sorted({(product_id, url) for product_id, url, _sha in identities.values()})
    repositories.bulk_create([
        repositories.model(product_id=product_id, url=url, provider=repository_provider(url))
        for product_id, url in repository_keys
    ], ignore_conflicts=True)
    repository_ids = {
        (product_id, url): pk
        for pk, product_id, url in matching_pairs(repositories, "product_id", "url", repository_keys)
        .values_list("pk", "product_id", "url")
    }

    engagement_keys = {
        pk: (repository_ids[product_id, url], sha)
        for pk, (product_id, url, sha) in identities.items()
    }
    commit_keys = sorted(set(engagement_keys.values()))
    commits.bulk_create([
        commits.model(repository_id=repository_id, sha=sha)
        for repository_id, sha in commit_keys
    ], ignore_conflicts=True)
    commit_ids = {
        (repository_id, sha): pk
        for pk, repository_id, sha in matching_pairs(commits, "repository_id", "sha", commit_keys)
        .values_list("pk", "repository_id", "sha")
    }
    return engagements.bulk_update([
        engagements.model(pk=pk, commit_id=commit_ids[key])
        for pk, key in engagement_keys.items()
    ], ["commit"])


def backfill_engagement_commits(apps, schema_editor):
    connection = schema_editor.connection
    alias = connection.alias
    engagement = apps.get_model("dojo", "Engagement")
    repository = apps.get_model("dojo", "Repository")
    commit = apps.get_model("dojo", "Commit")
    repositories = repository.objects.using(alias).order_by()
    commits = commit.objects.using(alias).order_by()
    unlinked = engagement.objects.using(alias).filter(
        commit__isnull=True,
        source_code_management_uri__isnull=False,
        commit_hash__isnull=False,
    ).exclude(source_code_management_uri="").exclude(commit_hash="")
    upper_pk = unlinked.order_by("-pk").values_list("pk", flat=True).first()
    if upper_pk is None:
        return

    last_pk = None
    updated = 0
    remaining = unlinked.filter(pk__lte=upper_pk)
    while True:
        with transaction.atomic(using=alias):
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout = '2s'")
                cursor.execute("SET LOCAL statement_timeout = '30s'")
            batch = remaining if last_pk is None else remaining.filter(pk__gt=last_pk)
            rows = list(
                batch.order_by("pk").select_for_update(no_key=True)
                .values_list("pk", "product_id", "source_code_management_uri", "commit_hash")[:BATCH_SIZE],
            )
            if not rows:
                break
            updated += link_batch(unlinked, repositories, commits, rows)
            last_pk = rows[-1][0]

    logger.info("Backfilled SCM commit links for %d engagements", updated)


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("dojo", "0308_aspm_scm_engagement_constraints")]
    operations = [
        # Unlinking selectively on rollback cannot distinguish backfill and user edits.
        migrations.RunPython(backfill_engagement_commits, migrations.RunPython.noop),
    ]
