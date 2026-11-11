from django.test import SimpleTestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from dojo.finding.api.large_offset_pagination import FindingLargeOffsetPagination


class FindingPaginationCollectionsTests(SimpleTestCase):
    def test_delete_preview_list_uses_standard_pagination(self):
        for fast in ("0", "1"):
            with self.subTest(fast=fast):
                request = Request(APIRequestFactory().get("/api/v2/findings/1/delete_preview/", {"limit": 2, "offset": 1, "fast_offset": fast}))
                paginator = FindingLargeOffsetPagination()
                self.assertEqual(paginator.paginate_queryset([1, 2, 3, 4], request), [2, 3])
                self.assertEqual(paginator.count, 4)

    def test_collection_deep_offset_does_not_enter_orm_fast_path(self):
        request = Request(APIRequestFactory().get("/", {"limit": 2, "offset": 5000, "fast_offset": "1"}))
        self.assertEqual(FindingLargeOffsetPagination().paginate_queryset(list(range(5005)), request), [5000, 5001])
