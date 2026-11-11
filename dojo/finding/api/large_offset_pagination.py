from rest_framework.pagination import LimitOffsetPagination


class FindingLargeOffsetPagination(LimitOffsetPagination):
    """
    Experimental two-stage pagination for Finding API.

    Optimizes deep offsets with ascending primary-key
    ordering while keeping the standard API response.
    """

    def paginate_queryset(self, queryset, request, view=None):
        offset = self.get_offset(request)

        explicit_order = tuple(queryset.query.order_by)
        default_order = tuple(
            queryset.model._meta.ordering or ()
        )
        ordering = explicit_order or default_order

        # Preserve standard behavior unless explicitly enabled.
        # Other orderings can require different handling.
        if (
            request.query_params.get("fast_offset") != "1"
            or offset < 5000
            or ordering not in (("id",), ("pk",))
            or not queryset.query.standard_ordering
            or queryset.query.extra_order_by
        ):
            return super().paginate_queryset(
                queryset, request, view=view
            )

        self.request = request
        self.limit = self.get_limit(request)

        if self.limit is None:
            return None

        self.offset = offset
        self.count = self.get_count(queryset)

        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset >= self.count:
            return []

        # Phase 1: fetch only primary keys.
        ids = list(
            queryset.values_list("pk", flat=True)[
                offset:offset + self.limit
            ]
        )

        if not ids:
            return []

        # Phase 2: fetch complete authorized findings.
        # Original filters and prefetch configuration remain.
        return list(
            queryset.filter(pk__in=ids).order_by("pk")
        )
