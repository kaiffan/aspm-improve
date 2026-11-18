"""Differential metrics oracle with a frozen RC4 reference and a bounded-row guard."""
import calendar as tcalendar
from collections import OrderedDict
from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone

from dojo import query_hooks
from dojo.models import Endpoint, Endpoint_Status, Finding, User
from dojo.product.ui import views
from dojo.utils import calculate_finding_age, get_zero_severity_level, sum_by_severity_level
from unittests import test_product_metrics_closed_count as closed_tests

FROZEN_RC4_VIEW = 'def view_product_metrics(request, pid):\n    prod = get_object_or_404(Product, id=pid)\n    engs = Engagement.objects.filter(product=prod, active=True)\n    view = identify_view(request)\n\n    filter_string_matching = get_system_setting("filter_string_matching", False)\n    filter_class = EngagementFilterWithoutObjectLookups if filter_string_matching else EngagementFilter\n    result = filter_class(\n        request.GET,\n        queryset=Engagement.objects.filter(product=prod, active=False).order_by("-target_end"))\n\n    inactive_engs_page = get_page_items(request, result.qs, 10)\n\n    filters = {}\n    if view == "Finding":\n        filters = finding_queries(request, prod)\n    # TODO: Delete this after the move to Locations\n    elif view == "Endpoint":\n        filters = endpoint_queries(request, prod)\n\n    start_date = timezone.make_aware(datetime.combine(filters["start_date"], datetime.min.time()))\n    end_date = filters["end_date"]\n\n    r = relativedelta(end_date, start_date)\n    weeks_between = ceil((((r.years * 12) + r.months) * 4.33) + (r.days / 7))\n    if weeks_between <= 0:\n        weeks_between += 2\n\n    punchcard, ticks = get_punchcard_data(filters.get("open", None), start_date, weeks_between, view)\n\n    add_breadcrumb(parent=prod, top_level=False, request=request)\n\n    # An ordered dict does not make sense here.\n    open_close_weekly = OrderedDict()\n    severity_weekly = OrderedDict()\n    critical_weekly = OrderedDict()\n    high_weekly = OrderedDict()\n    medium_weekly = OrderedDict()\n    open_objs_by_age = {}\n\n    open_objs_by_severity = get_zero_severity_level()\n    closed_objs_by_severity = get_zero_severity_level()\n    accepted_objs_by_severity = get_zero_severity_level()\n\n    # Optimization: Make all queries lists, and only pull values of fields for metrics based calculations\n    open_vulnerabilities = list(filters["open_vulns"].values("cwe", "count"))\n    all_vulnerabilities = list(filters["all_vulns"].values("cwe", "count"))\n\n    verified_objs_by_severity = list(filters.get("verified").values("severity"))\n    inactive_objs_by_severity = list(filters.get("inactive").values("severity"))\n    false_positive_objs_by_severity = list(filters.get("false_positive").values("severity"))\n    out_of_scope_objs_by_severity = list(filters.get("out_of_scope").values("severity"))\n    new_objs_by_severity = list(filters.get("new_verified").values("severity"))\n    all_objs_by_severity = list(filters.get("all").values("severity"))\n\n    all_findings = list(filters.get("all", []).values("id", "date", "severity"))\n    open_findings = list(filters.get("open", []).values("id", "date", "mitigated", "severity"))\n    # Include mitigated date for closed findings to group by when they were closed, not discovered\n    closed_findings = list(filters.get("closed", []).values("id", "date", "mitigated", "severity"))\n    accepted_findings = list(filters.get("accepted", []).values("id", "date", "severity"))\n\n    """\n        Optimization: Create dictionaries in the structure of { finding_id: True } for index based search\n        Previously the for-loop below used "if finding in open_findings" -- an average O(n^2) time complexity\n        This allows for "if open_findings.get(finding_id, None)" -- an average O(n) time complexity\n    """\n    open_findings_dict = {f.get("id"): True for f in open_findings}\n    closed_findings_dict = {f.get("id"): True for f in closed_findings}\n    accepted_findings_dict = {f.get("id"): True for f in accepted_findings}\n\n    for finding in all_findings:\n        iso_cal = finding.get("date").isocalendar()\n        date = iso_to_gregorian(iso_cal[0], iso_cal[1], 1)\n        html_date = date.strftime("<span class=\'small\'>%m/%d<br/>%Y</span>")\n        unix_timestamp = (tcalendar.timegm(date.timetuple()) * 1000)\n\n        # Open findings\n        if open_findings_dict.get(finding.get("id", None)):\n            if unix_timestamp not in critical_weekly:\n                critical_weekly[unix_timestamp] = {"count": 0, "week": html_date}\n            if unix_timestamp not in high_weekly:\n                high_weekly[unix_timestamp] = {"count": 0, "week": html_date}\n            if unix_timestamp not in medium_weekly:\n                medium_weekly[unix_timestamp] = {"count": 0, "week": html_date}\n\n            if unix_timestamp in open_close_weekly:\n                open_close_weekly[unix_timestamp]["open"] += 1\n            else:\n                open_close_weekly[unix_timestamp] = {"closed": 0, "open": 1, "accepted": 0}\n                open_close_weekly[unix_timestamp]["week"] = html_date\n\n            if view in {"Finding", "Endpoint"}:\n                severity = finding.get("severity")\n\n            finding_age = calculate_finding_age(finding)\n            if open_objs_by_age.get(finding_age):\n                open_objs_by_age[finding_age] += 1\n            else:\n                open_objs_by_age[finding_age] = 1\n\n            if unix_timestamp in severity_weekly:\n                if severity in severity_weekly[unix_timestamp]:\n                    severity_weekly[unix_timestamp][severity] += 1\n                else:\n                    severity_weekly[unix_timestamp][severity] = 1\n            else:\n                severity_weekly[unix_timestamp] = get_zero_severity_level()\n                severity_weekly[unix_timestamp][severity] = 1\n                severity_weekly[unix_timestamp]["week"] = html_date\n\n            if severity == "Critical":\n                if unix_timestamp in critical_weekly:\n                    critical_weekly[unix_timestamp]["count"] += 1\n                else:\n                    critical_weekly[unix_timestamp] = {"count": 1, "week": html_date}\n            elif severity == "High":\n                if unix_timestamp in high_weekly:\n                    high_weekly[unix_timestamp]["count"] += 1\n                else:\n                    high_weekly[unix_timestamp] = {"count": 1, "week": html_date}\n            elif severity == "Medium":\n                if unix_timestamp in medium_weekly:\n                    medium_weekly[unix_timestamp]["count"] += 1\n                else:\n                    medium_weekly[unix_timestamp] = {"count": 1, "week": html_date}\n            # Optimization: count severity level on server side\n            if open_objs_by_severity.get(finding.get("severity")) is not None:\n                open_objs_by_severity[finding.get("severity")] += 1\n\n        # Close findings - group by mitigated date, not discovery date\n        elif closed_findings_dict.get(finding.get("id", None)):\n            # Find the closed finding to get its mitigated date\n            closed_finding = next((f for f in closed_findings if f.get("id") == finding.get("id")), None)\n            if closed_finding and closed_finding.get("mitigated"):\n                # Use mitigated date for grouping closed findings\n                mitigated_date = closed_finding.get("mitigated")\n                mitigated_date_only = mitigated_date.date() if isinstance(mitigated_date, datetime) else mitigated_date\n                iso_cal = mitigated_date_only.isocalendar()\n                mitigated_week_start = iso_to_gregorian(iso_cal[0], iso_cal[1], 1)\n                mitigated_html_date = mitigated_week_start.strftime("<span class=\'small\'>%m/%d<br/>%Y</span>")\n                mitigated_unix_timestamp = (tcalendar.timegm(mitigated_week_start.timetuple()) * 1000)\n\n                if mitigated_unix_timestamp in open_close_weekly:\n                    open_close_weekly[mitigated_unix_timestamp]["closed"] += 1\n                else:\n                    open_close_weekly[mitigated_unix_timestamp] = {"closed": 1, "open": 0, "accepted": 0}\n                    open_close_weekly[mitigated_unix_timestamp]["week"] = mitigated_html_date\n            elif unix_timestamp in open_close_weekly:\n                # Fallback to discovery date if mitigated date is not available\n                open_close_weekly[unix_timestamp]["closed"] += 1\n            else:\n                # Fallback to discovery date if mitigated date is not available\n                open_close_weekly[unix_timestamp] = {"closed": 1, "open": 0, "accepted": 0}\n                open_close_weekly[unix_timestamp]["week"] = html_date\n            # Optimization: count severity level on server side\n            if closed_objs_by_severity.get(finding.get("severity")) is not None:\n                closed_objs_by_severity[finding.get("severity")] += 1\n\n        # Risk Accepted findings\n        if accepted_findings_dict.get(finding.get("id", None)):\n            if unix_timestamp in open_close_weekly:\n                open_close_weekly[unix_timestamp]["accepted"] += 1\n            else:\n                open_close_weekly[unix_timestamp] = {"closed": 0, "open": 0, "accepted": 1}\n                open_close_weekly[unix_timestamp]["week"] = html_date\n            # Optimization: count severity level on server side\n            if accepted_objs_by_severity.get(finding.get("severity")) is not None:\n                accepted_objs_by_severity[finding.get("severity")] += 1\n\n    tests = Test.objects.filter(engagement__product=prod).prefetch_related("finding_set", "test_type")\n    verified_finding_subquery = build_count_subquery(\n        Finding.objects.filter(test=OuterRef("pk"), verified=True),\n        group_field="test_id",\n    )\n    tests = tests.annotate(verified_finding_count=Coalesce(verified_finding_subquery, Value(0)))\n\n    test_data = {}\n    for t in tests:\n        if t.test_type.name in test_data:\n            test_data[t.test_type.name] += t.verified_finding_count\n        else:\n            test_data[t.test_type.name] = t.verified_finding_count\n\n    # Optimization: Format Open/Total CWE vulnerabilities graph data here, instead of template\n    open_vulnerabilities = [["CWE-" + str(f.get("cwe")), f.get("count")] for f in open_vulnerabilities]\n    all_vulnerabilities = [["CWE-" + str(f.get("cwe")), f.get("count")] for f in all_vulnerabilities]\n\n    product_tab = Product_Tab(prod, title=str(labels.ASSET_LABEL), tab="metrics")\n\n    return render(request, "dojo/product_metrics.html", {\n        "prod": prod,\n        "product_tab": product_tab,\n        "engs": engs,\n        "inactive_engs": inactive_engs_page,\n        "view": view,\n        "verified_objs": len(verified_objs_by_severity),\n        "verified_objs_by_severity": sum_by_severity_level(verified_objs_by_severity),\n        "open_objs": len(open_findings),\n        "open_objs_by_severity": open_objs_by_severity,\n        "open_objs_by_age": open_objs_by_age,\n        "inactive_objs": len(inactive_objs_by_severity),\n        "inactive_objs_by_severity": sum_by_severity_level(inactive_objs_by_severity),\n        "closed_objs": len(closed_findings),\n        "closed_objs_by_severity": closed_objs_by_severity,\n        "false_positive_objs": len(false_positive_objs_by_severity),\n        "false_positive_objs_by_severity": sum_by_severity_level(false_positive_objs_by_severity),\n        "out_of_scope_objs": len(out_of_scope_objs_by_severity),\n        "out_of_scope_objs_by_severity": sum_by_severity_level(out_of_scope_objs_by_severity),\n        "accepted_objs": len(accepted_findings),\n        "accepted_objs_by_severity": accepted_objs_by_severity,\n        "new_objs": len(new_objs_by_severity),\n        "new_objs_by_severity": sum_by_severity_level(new_objs_by_severity),\n        "all_objs": len(all_objs_by_severity),\n        "all_objs_by_severity": sum_by_severity_level(all_objs_by_severity),\n        "form": filters.get("form", None),\n        "reset_link": reverse("view_product_metrics", args=(prod.id,)) + "?type=" + view,\n        "open_vulnerabilities_count": len(open_vulnerabilities),\n        "open_vulnerabilities": open_vulnerabilities,\n        "all_vulnerabilities_count": len(all_vulnerabilities),\n        "all_vulnerabilities": all_vulnerabilities,\n        "start_date": start_date,\n        "punchcard": punchcard,\n        "ticks": ticks,\n        "open_close_weekly": open_close_weekly,\n        "severity_weekly": severity_weekly,\n        "critical_weekly": critical_weekly,\n        "high_weekly": high_weekly,\n        "medium_weekly": medium_weekly,\n        "test_data": test_data,\n        "user": request.user})\n\n'


class ProductMetrics(closed_tests.ProductMetricsClosedCountTest):
    def context(self, func=views.view_product_metrics, params=None):
        request = RequestFactory().get(reverse("view_product_metrics", args=[self.product.pk]), params or {"date": "7"})
        request.user = self.user
        request.session = {}
        with patch.object(views, "render", side_effect=lambda _request, _template, context: context):
            return func(request, self.product.pk)

    def reference(self, params=None):
        namespace = {**vars(views), "tcalendar": tcalendar, "OrderedDict": OrderedDict, "get_zero_severity_level": get_zero_severity_level, "calculate_finding_age": calculate_finding_age, "sum_by_severity_level": sum_by_severity_level, "render": lambda _request, _template, context: context}
        exec(compile(FROZEN_RC4_VIEW, "frozen-940a40f1-product-metrics", "exec"), namespace)  # noqa: S102 -- frozen repository reference, never user input
        return self.context(namespace["view_product_metrics"], params)

    def fixture(self):
        cases = [
            ("Critical", date(2024, 12, 30), None, True, False),
            ("High", date(2024, 12, 31), None, True, False),
            ("Low", date(2024, 12, 31), datetime(2025, 1, 6, 0, 1, tzinfo=ZoneInfo("UTC")), False, False),
            ("Info", date(2024, 12, 31), datetime(2025, 1, 5, 23, 59, tzinfo=ZoneInfo("UTC")), False, False),
            ("Medium", date(2025, 1, 2), None, False, True),
        ]
        for i, (severity, discovered, mitigated, active, accepted) in enumerate(cases):
            finding = Finding.objects.create(title="Metric " + str(i), test=self.test, severity=severity, date=discovered, reporter=self.user, cwe=79, verified=True)
            Finding.objects.filter(pk=finding.pk).update(active=active, risk_accepted=accepted, is_mitigated=bool(mitigated), mitigated=mitigated)

    def compare(self, params=None):
        expected = self.reference(params)
        actual = self.context(params=params)
        keys = [key for key in expected if "_objs" in key or key.endswith("weekly") or "vulnerabilities" in key or key in {"test_data", "punchcard", "ticks"}]
        self.assertEqual({k: actual[k] for k in keys}, {k: expected[k] for k in keys})

    def test_complete_chart_parity(self):
        self.fixture()
        self.compare()
        actual = self.context()
        self.assertEqual(sum(row["closed"] for row in actual["open_close_weekly"].values()), 2)
        self.assertEqual(actual["all_objs"], 5)

    def test_empty_chart_parity(self):
        self.compare()

    def test_filter_and_timezone_parity(self):
        self.fixture()
        with timezone.override(ZoneInfo("America/Los_Angeles")):
            self.compare()
            self.compare({"date": "7", "severity": "High"})

    def test_no_finding_materialization(self):
        Finding.objects.bulk_create([Finding(title="Bounded", test=self.test, severity="High", date=date(2024, 1, 1), active=True, reporter=self.user) for _ in range(2000)], batch_size=500)
        created = []
        real = Finding.from_db

        def count(*args, **kwargs):
            instance = real(*args, **kwargs)
            created.append(instance.pk)
            return instance
        with patch.object(Finding, "from_db", side_effect=count):
            actual = self.context()
        self.assertEqual(actual["open_objs"], 2000)
        self.assertLess(len(created), 20, "Product Metrics loaded Finding models instead of aggregate buckets")
        self.assertEqual(sum(v["open"] for v in actual["open_close_weekly"].values()), 2000)

    def test_product_rbac(self):
        self.fixture()
        outsider = User.objects.create_user(username="metrics_outsider", password="test")  # noqa: S106 -- fixture user
        self.client.force_login(outsider)
        self.assertIn(self.client.get(reverse("view_product_metrics", args=[self.product.pk])).status_code, [400, 403])
        self.product.authorized_users.add(outsider.pk)
        self.assertEqual(self.client.get(reverse("view_product_metrics", args=[self.product.pk])).status_code, 200)

    @override_settings(V3_FEATURE_LOCATIONS=False)
    def test_endpoint_closed_week_uses_mitigation_time(self):
        finding = Finding.objects.create(title="Endpoint metric", test=self.test, severity="High", date=date(2024, 1, 1), active=True, reporter=self.user)
        endpoint = Endpoint.objects.create(host="metrics.example.invalid", product=self.product)
        Endpoint_Status.objects.create(endpoint=endpoint, finding=finding, date=date(2024, 1, 1), mitigated=True, mitigated_time=datetime(2025, 1, 6, 0, 1, tzinfo=ZoneInfo("UTC")))
        context = self.context(params={"date": "7", "type": "Endpoint"})
        self.assertEqual(context["all_objs"], 1)
        self.assertEqual(context["closed_objs"], 1)
        weeks = list(context["open_close_weekly"].values())
        self.assertEqual(len(weeks), 1)
        self.assertEqual(weeks[0]["closed"], 1)
        self.assertIn("01/06", weeks[0]["week"])

    def test_test_type_counts_preserve_finding_manager_scope(self):
        self.fixture()
        hidden = Finding.objects.filter(test=self.test).first()
        with patch.dict(query_hooks._DEFAULT_QUERYSET_FILTERS, {"dojo.finding": {"rc5-hide": lambda qs: qs.exclude(pk=hidden.pk)}}):
            self.compare()
