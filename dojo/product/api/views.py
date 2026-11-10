from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, OuterRef, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import dojo.api_v2.mixins as dojo_mixins
from dojo.api_v2 import prefetch
from dojo.api_v2 import serializers as api_v2_serializers
from dojo.api_v2.views import (
    DeprecationNoticeMixin,
    PrefetchDojoModelViewSet,
    report_generate_response,
    schema_with_prefetch,
)
from dojo.authorization import api_permissions as permissions
from dojo.models import Endpoint, Finding, Product, Product_API_Scan_Configuration
from dojo.product.api.filters import ApiProductFilter
from dojo.product.api.serializer import (
    ProductAPIScanConfigurationSerializer,
    ProductFindingCountSerializer,
    ProductSerializer,
    ProductSummarySerializer,
)
from dojo.product.queries import (
    get_authorized_product_api_scan_configurations,
    get_authorized_products,
)
from dojo.query_utils import build_count_subquery
from dojo.utils import async_delete, get_setting


# Authorization: object-based
@extend_schema_view(**schema_with_prefetch())
class ProductAPIScanConfigurationViewSet(
    DeprecationNoticeMixin,
    PrefetchDojoModelViewSet,
):
    deprecation = "api_scan_configuration"
    serializer_class = ProductAPIScanConfigurationSerializer
    queryset = Product_API_Scan_Configuration.objects.none()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = [
        "id",
        "product",
        "tool_configuration",
        "service_key_1",
        "service_key_2",
        "service_key_3",
    ]
    permission_classes = (
        IsAuthenticated,
        permissions.UserHasProductAPIScanConfigurationPermission,
    )

    def get_queryset(self):
        return get_authorized_product_api_scan_configurations(
            "view",
        )


_findings_parameter = OpenApiParameter(
    "findings",
    str,
    enum=["full", "count", "none"],
    default="full",
    description="With count, return the exact active findings count without finding IDs. "
    "With none, omit both findings_count and findings_list. "
    "Full includes both fields and is the default.",
)


@extend_schema_view(**schema_with_prefetch())
@extend_schema_view(
    list=extend_schema(parameters=[_findings_parameter]),
    retrieve=extend_schema(parameters=[_findings_parameter]),
)
class ProductViewSet(
    prefetch.PrefetchListMixin,
    prefetch.PrefetchRetrieveMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
    dojo_mixins.DeletePreviewModelMixin,
):
    serializer_class = ProductSerializer
    queryset = Product.objects.none()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ApiProductFilter
    permission_classes = (
        IsAuthenticated,
        permissions.UserHasProductPermission,
    )

    def get_queryset(self):
        products = (
            get_authorized_products("view")
            .select_related(
                # SlugRelatedField reads .value on the related object — without
                # select_related each product fires a separate lookup query.
                "platform",
                "lifecycle",
                "origin",
            )
            .prefetch_related(
                "tags",
                "product_meta",
                "authorized_users",
                "regulations",
            )
            .distinct()
        )
        if self.action in {"list", "retrieve"}:
            return products

        base_findings = Finding.objects.filter(
            test__engagement__product_id=OuterRef("pk"),
            active=True,
        )
        return products.annotate(
            active_finding_count=Coalesce(
                build_count_subquery(base_findings, group_field="test__engagement__product_id"),
                Value(0),
            ),
        )

    def _findings_mode(self):
        if self.action in {"list", "retrieve"} and self.request is not None:
            return self.request.query_params.get("findings")
        return None

    def get_serializer_class(self):
        mode = self._findings_mode()
        if mode == "count":
            return ProductFindingCountSerializer
        if mode == "none":
            return ProductSummarySerializer
        return super().get_serializer_class()

    def get_object(self):
        product = super().get_object()
        if self.action == "retrieve":
            self._load_findings_fields([product])
        return product

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        if self.action == "list" and page:
            self._load_findings_fields(page)
        return page

    def _load_findings_fields(self, products):
        mode = self._findings_mode()
        if mode == "none":
            return

        # Read findings only for products that passed authorization and filtering.
        active_findings = (
            Finding.objects.filter(
                test__engagement__product_id__in=[product.pk for product in products],
                active=True,
            )
            .order_by()
            .values_list("test__engagement__product_id")
        )
        if mode == "count":
            counts_by_product = dict(active_findings.annotate(count=Count("*")))
            for product in products:
                product.active_finding_count = counts_by_product.get(product.pk, 0)
            return

        # Use the ordered ID lists for both fields in the full response.
        ids_by_product = dict(active_findings.annotate(finding_ids=ArrayAgg("pk", order_by="pk")))
        for product in products:
            product.prefetched_active_finding_ids = ids_by_product.get(product.pk, [])
            product.active_finding_count = len(product.prefetched_active_finding_ids)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if get_setting("ASYNC_OBJECT_DELETE"):
            async_del = async_delete()
            async_del.delete(instance)
        else:
            with Endpoint.allow_endpoint_init():  # TODO: Delete this after the move to Locations
                instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # def list(self, request):
    #     # Note the use of `get_queryset()` instead of `self.queryset`
    #     queryset = self.get_queryset()
    #     serializer = self.serializer_class(queryset, many=True)
    #     return Response(serializer.data)

    @extend_schema(
        request=api_v2_serializers.ReportGenerateOptionSerializer,
        responses={status.HTTP_200_OK: api_v2_serializers.ReportGenerateSerializer},
    )
    @action(
        detail=True, methods=["post"],
        # IsAuthenticated only: report generation requires View permission,
        # enforced by the permission-filtered get_queryset(). The viewset's
        # permission_classes would check Edit (POST), which is too restrictive.
        permission_classes=[IsAuthenticated],
    )
    def generate_report(self, request, pk=None):
        product = self.get_object()

        options = {}
        # prepare post data
        report_options = api_v2_serializers.ReportGenerateOptionSerializer(
            data=request.data,
        )
        if report_options.is_valid():
            options["include_finding_notes"] = report_options.validated_data[
                "include_finding_notes"
            ]
            options["include_finding_images"] = report_options.validated_data[
                "include_finding_images"
            ]
            options[
                "include_executive_summary"
            ] = report_options.validated_data["include_executive_summary"]
            options[
                "include_table_of_contents"
            ] = report_options.validated_data["include_table_of_contents"]
            options["report_type"] = report_options.validated_data["report_type"]
        else:
            return Response(
                report_options.errors, status=status.HTTP_400_BAD_REQUEST,
            )

        return report_generate_response(request, product, options)
