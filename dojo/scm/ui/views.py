from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import F
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _

from dojo.aspm_ingestion.permissions import api_only_scans_enabled
from dojo.models import Engagement
from dojo.product.queries import get_authorized_products
from dojo.scm.queries import authorized_commits, authorized_repositories, compare_findings
from dojo.scm.ui.forms import COMPARISON_CATEGORIES, CompareCommitsForm
from dojo.utils import Product_Tab

PAGE_SIZE = 25
COMMIT_ORDER = (F("committed_at").desc(nulls_last=True), "-pk")


def _page(request, queryset):
    return Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("page"))


def _project_context(product, title):
    return {
        "product_tab": Product_Tab(product, title=title, tab="repositories"),
        "title": title,
    }


def repository_list(request, product_id):
    product = get_object_or_404(get_authorized_products("view", user=request.user), pk=product_id)
    title = _("Repositories")
    return render(request, "dojo/scm/repository_list.html", {
        **_project_context(product, title),
        "custom_breadcrumb": {product.name: reverse("view_product", args=(product.pk,))},
        "repositories": _page(request, product.repositories.order_by("url", "pk")),
    })


def repository_detail(request, repository_id):
    repository = get_object_or_404(authorized_repositories(request.user), pk=repository_id)
    return render(request, "dojo/scm/repository_detail.html", {
        **_project_context(repository.product, repository.url),
        "repository": repository,
        "commits": _page(request, repository.commits.order_by(*COMMIT_ORDER)),
        "custom_breadcrumb": _repository_breadcrumbs(repository),
    })


def _repository_breadcrumbs(repository):
    product = repository.product
    return {
        product.name: reverse("view_product", args=(product.pk,)),
        _("Repositories"): reverse("scm_repository_list", args=(product.pk,)),
    }


def _commit_breadcrumbs(commit):
    return {
        **_repository_breadcrumbs(commit.repository),
        commit.repository.url: reverse("scm_repository_detail", args=(commit.repository_id,)),
    }


def commit_detail(request, commit_id):
    if api_only_scans_enabled():
        from dojo.aspm_ingestion.ui.views import commit_evidence  # noqa: PLC0415 -- historical evidence surface

        return commit_evidence(request, commit_id)
    commit = get_object_or_404(authorized_commits(request.user), pk=commit_id)
    product = commit.repository.product
    engagements = Engagement.objects.filter(commit=commit, product=product).order_by("-pk")
    return render(request, "dojo/scm/commit_detail.html", {
        **_project_context(product, commit.sha[:12]),
        "commit": commit,
        "engagements": _page(request, engagements),
        "recent_commits": commit.repository.commits.exclude(pk=commit.pk).order_by(*COMMIT_ORDER)[:PAGE_SIZE],
        "custom_breadcrumb": _commit_breadcrumbs(commit),
    })


def commit_compare(request, commit_id):
    commit = get_object_or_404(authorized_commits(request.user), pk=commit_id)
    form = CompareCommitsForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest(_("Choose a valid base commit and comparison category."))
    base = get_object_or_404(commit.repository.commits.exclude(pk=commit.pk), pk=form.cleaned_data["base"])
    if api_only_scans_enabled():
        from dojo.aspm_ingestion.ui.views import commit_evidence  # noqa: PLC0415 -- optional historical evidence layer

        return commit_evidence(request, commit_id, section="changes")
    category = form.cleaned_data["category"] or "new"
    findings, next_id = compare_findings(
        request.user, base, commit, category, after=form.cleaned_data["after"] or 0, page_size=PAGE_SIZE,
    )
    params = {"base": base.pk, "category": category}
    return render(request, "dojo/scm/commit_compare.html", {
        **_project_context(commit.repository.product, _("Compare commits")),
        "commit": commit,
        "base_commit": base,
        "findings": findings,
        "categories": [(key, label, f"?{urlencode({**params, 'category': key})}") for key, label in COMPARISON_CATEGORIES],
        "category": category,
        "next_url": f"?{urlencode({**params, 'after': next_id})}" if next_id else None,
        "custom_breadcrumb": {
            **_commit_breadcrumbs(commit),
            commit.sha[:12]: reverse("scm_commit_detail", args=(commit.pk,)),
        },
    })
