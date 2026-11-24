from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated

from dojo.api_v2.views import DojoModelViewSet
from dojo.authorization.authorization import user_has_permission_or_403
from dojo.scm.api.filters import CommitFilter, RepositoryFilter
from dojo.scm.api.serializer import CommitSerializer, RepositorySerializer
from dojo.scm.models import Commit, Repository
from dojo.scm.queries import authorized_commits, authorized_repositories


class ProductScopedSCMViewSet(DojoModelViewSet):
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        instance = super().get_object()
        if self.action == "delete_preview":
            user_has_permission_or_403(self.request.user, self.product_for_instance(instance), "delete")
        return instance

    def perform_create(self, serializer):
        user_has_permission_or_403(self.request.user, self.product_for_create(serializer.validated_data), "add")
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError as error:
            if getattr(getattr(error.__cause__, "diag", None), "constraint_name", None) != self.identity_constraint:
                raise
            msg = "An object with this identity already exists."
            raise serializers.ValidationError(msg) from error

    def perform_update(self, serializer):
        user_has_permission_or_403(self.request.user, self.product_for_instance(serializer.instance), "edit")
        serializer.save()

    def perform_destroy(self, instance):
        user_has_permission_or_403(self.request.user, self.product_for_instance(instance), "delete")
        instance.delete()


class RepositoryViewSet(ProductScopedSCMViewSet):
    queryset = Repository.objects.none()
    serializer_class = RepositorySerializer
    filterset_class = RepositoryFilter
    identity_constraint = "aspm_repository_product_url_uniq"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        return authorized_repositories(self.request.user).order_by("pk")

    def product_for_create(self, data):
        return data["product"]

    def product_for_instance(self, repository):
        return repository.product


class CommitViewSet(ProductScopedSCMViewSet):
    queryset = Commit.objects.none()
    serializer_class = CommitSerializer
    filterset_class = CommitFilter
    identity_constraint = "aspm_commit_repository_sha_uniq"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        return authorized_commits(self.request.user).order_by("pk")

    def product_for_create(self, data):
        return data["repository"].product

    def product_for_instance(self, commit):
        return commit.repository.product
