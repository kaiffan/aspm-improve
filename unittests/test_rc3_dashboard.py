from datetime import datetime, timedelta

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from unittests import test_round4_performance as round4
from unittests.dojo_test_case import DojoTestCase, versioned_fixtures


@versioned_fixtures
class TestRC3Dashboard(DojoTestCase):
    fixtures = ["dojo_testdata.json"]
    setUp = round4.TestRound4Performance.setUp

    def test_weekly_counters_keep_timezone_boundaries_in_one_narrow_aggregate(self):
        self.client.force_login(self.reader)
        for zone in ("UTC", "America/New_York"):
            with self.subTest(zone=zone), timezone.override(zone):
                today = timezone.now().date()
                start = timezone.make_aware(datetime.combine(today - timedelta(days=7), datetime.min.time()))
                end = timezone.make_aware(datetime.combine(today + timedelta(days=1), datetime.min.time()))
                for finding, when in zip(self.findings, (start - timedelta(microseconds=1), start, end), strict=True):
                    self.scope.filter(pk=finding.pk).update(date=when.date(), mitigated=when)
                expected_new = self.scope.filter(date__range=[today - timedelta(days=7), today]).values("pk").distinct().count()
                expected_mitigated = self.scope.filter(mitigated__date__range=[today - timedelta(days=7), today]).values("pk").distinct().count()
                with CaptureQueriesContext(connection) as queries:
                    response = self.client.get(reverse("dashboard"))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["finding_count"], expected_new)
                self.assertEqual(response.context["mitigated_count"], expected_mitigated)
                aggregates = [q["sql"] for q in queries if 'AS "finding_count"' in q["sql"] and 'AS "mitigated_count"' in q["sql"]]
                self.assertEqual(len(aggregates), 1)
                self.assertNotIn('"description"', aggregates[0])
