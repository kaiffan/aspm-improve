from django.db.models import Count, IntegerField, Lookup, Subquery
from django.db.models.query import QuerySet


class TestIdInArray(Lookup):
    lookup_name = "test_id_in_array"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        return f"{lhs} = ANY({rhs})", (*lhs_params, *rhs_params)


def build_count_subquery(model_qs: QuerySet, group_field: str) -> Subquery:
    """Return a Subquery that yields one aggregated count per `group_field`."""
    # Important: slicing (`[:1]`) on an unordered queryset makes Django add an implicit `ORDER BY <pk>`.
    # With aggregation, Django then includes that pk in the GROUP BY, which collapses counts to 1.
    # Ordering by `group_field` avoids that and keeps the GROUP BY stable.
    model_qs = model_qs.order_by()
    return Subquery(
        model_qs.values(group_field).annotate(c=Count("pk")).order_by(group_field).values("c")[:1],  # one row per group_field
        output_field=IntegerField(),
    )
