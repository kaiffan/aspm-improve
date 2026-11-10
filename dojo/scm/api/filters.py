from django_filters import FilterSet, NumberFilter

from dojo.scm.models import Commit, Repository


class RepositoryFilter(FilterSet):
    product = NumberFilter(field_name="product_id")

    class Meta:
        model = Repository
        fields = ("product", "url", "provider", "default_branch", "external_id")


class CommitFilter(FilterSet):
    product = NumberFilter(field_name="repository__product_id")
    repository = NumberFilter(field_name="repository_id")

    class Meta:
        model = Commit
        fields = ("repository", "sha", "branch")
