from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from dojo.models import Product
from dojo.product.queries import get_authorized_products
from dojo.scm.models import Commit, Repository, normalize_parent_shas, normalize_repository_url, normalize_sha


def _normalize(normalizer, value):
    try:
        return normalizer(value)
    except DjangoValidationError as error:
        raise serializers.ValidationError(error.messages) from error


class SCMIdentitySerializer(serializers.ModelSerializer):
    identity_fields = ()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance:
            changed = {
                name: "This field cannot be changed after creation."
                for name in self.identity_fields
                if name in attrs and attrs[name] != getattr(self.instance, name)
            }
            if changed:
                raise serializers.ValidationError(changed)
        return attrs

    def viewable_products(self):
        user = getattr(self.context.get("request"), "user", None)
        return get_authorized_products("view", user=user) if user and user.is_authenticated else Product.objects.none()


class RepositorySerializer(SCMIdentitySerializer):
    identity_fields = ("product", "url")
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.none())
    url = serializers.CharField(max_length=600)

    class Meta:
        model = Repository
        fields = ("id", "product", "url", "provider", "default_branch", "external_id", "metadata")

    def get_fields(self):
        fields = super().get_fields()
        fields["product"].queryset = self.viewable_products()
        return fields

    def validate_url(self, value):
        return _normalize(normalize_repository_url, value)

    def validate_metadata(self, value):
        if not isinstance(value, dict):
            msg = "Repository metadata must be a JSON object."
            raise serializers.ValidationError(msg)
        return value


class CommitSerializer(SCMIdentitySerializer):
    identity_fields = ("repository", "sha")
    repository = serializers.PrimaryKeyRelatedField(queryset=Repository.objects.none())
    sha = serializers.CharField(max_length=64)
    parent_shas = serializers.ListField(child=serializers.CharField(max_length=64), max_length=1000, required=False)

    class Meta:
        model = Commit
        fields = ("id", "repository", "sha", "branch", "author", "message", "committed_at", "parent_shas")

    def get_fields(self):
        fields = super().get_fields()
        fields["repository"].queryset = Repository.objects.filter(product__in=self.viewable_products()).select_related("product")
        return fields

    def validate_sha(self, value):
        return _normalize(normalize_sha, value)

    def validate_parent_shas(self, value):
        return _normalize(normalize_parent_shas, value)
