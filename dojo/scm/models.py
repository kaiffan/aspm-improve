from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from dojo.scm.identity_v1 import canonical_repository_url, canonical_sha


def normalize_repository_url(value):
    try:
        return canonical_repository_url(value)
    except ValueError as error:
        raise ValidationError(_("Enter an HTTP(S) repository URL with a path and without credentials, query, or fragment.")) from error


def normalize_sha(value):
    try:
        return canonical_sha(value)
    except ValueError as error:
        raise ValidationError(_("Enter a full Git commit SHA with 40 or 64 hexadecimal characters.")) from error


def normalize_parent_shas(value):
    if not isinstance(value, list) or len(value) > 1000:
        raise ValidationError(_("Provide a list of up to 1000 parent commit SHAs."))
    return [normalize_sha(sha) for sha in value]


class Repository(models.Model):
    class Provider(models.TextChoices):
        GITHUB = "github", "GitHub"
        GITLAB = "gitlab", "GitLab"
        BITBUCKET = "bitbucket", "Bitbucket"
        AZURE = "azure", "Azure Repos"
        OTHER = "other", _("Other")

    product = models.ForeignKey("dojo.Product", related_name="repositories", on_delete=models.CASCADE)
    url = models.CharField(max_length=600)
    provider = models.CharField(max_length=16, choices=Provider, default=Provider.OTHER)
    default_branch = models.CharField(max_length=150, blank=True)
    external_id = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("pk",)
        constraints = [models.UniqueConstraint(fields=("product", "url"), name="aspm_repository_product_url_uniq")]

    def __str__(self):
        return self.url

    def clean(self):
        super().clean()
        try:
            self.url = normalize_repository_url(self.url)
        except ValidationError as error:
            raise ValidationError({"url": error}) from error
        if not isinstance(self.metadata, dict):
            raise ValidationError({"metadata": _("Repository metadata must be a JSON object.")})

    def get_breadcrumbs(self):
        return [*self.product.get_breadcrumbs(), {"title": str(self), "url": reverse("scm_repository_detail", args=(self.pk,))}]


class Commit(models.Model):
    repository = models.ForeignKey(Repository, related_name="commits", on_delete=models.CASCADE)
    sha = models.CharField(max_length=64)
    branch = models.CharField(max_length=150, blank=True)
    author = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    committed_at = models.DateTimeField(null=True, blank=True)
    parent_shas = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ("-pk",)
        constraints = [models.UniqueConstraint(fields=("repository", "sha"), name="aspm_commit_repository_sha_uniq")]

    def __str__(self):
        return self.sha

    def clean(self):
        super().clean()
        try:
            self.sha = normalize_sha(self.sha)
        except ValidationError as error:
            raise ValidationError({"sha": error}) from error
        try:
            self.parent_shas = normalize_parent_shas(self.parent_shas)
        except ValidationError as error:
            raise ValidationError({"parent_shas": error}) from error

    def get_breadcrumbs(self):
        return [*self.repository.get_breadcrumbs(), {"title": self.sha[:12], "url": reverse("scm_commit_detail", args=(self.pk,))}]
