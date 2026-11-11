from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, override_settings

from dojo import context_processors
from dojo.aspm.branding import get_branding
from dojo.product_announcements import ErrorPageProductAnnouncement


class TestASPMBranding(SimpleTestCase):
    def test_release_metadata_is_local_and_does_not_need_database(self):
        brand = get_branding()
        self.assertEqual((brand["version"], brand["channel"], brand["upstream_version"]), ("1.0.1", "rc1", "3.5.100"))
        self.assertEqual(brand["name"], "ASPM")
        self.assertEqual(brand["mark"], "dojo/img/aspm-mark.svg")

    @override_settings(ASPM_BRAND_NAME='<script>alert("x")</script>', ASPM_BRAND_MARK="custom/mark.svg")
    def test_brand_can_be_replaced_and_template_escapes_name(self):
        brand = get_branding()
        html = render_to_string("dojo/aspm/brand.html", {"ASPM": brand})
        self.assertIn("custom/mark.svg", html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    @override_settings(ASPM_BRAND_MARK="https://example.invalid/logo.svg")
    def test_brand_assets_remain_local(self):
        with self.assertRaises(ImproperlyConfigured):
            get_branding()

    @override_settings(ASPM_SHOW_UPSTREAM_PROMOTIONS=False)
    def test_promos_are_not_fetched_and_read_only_warning_is_preserved(self):
        request = RequestFactory().get("/")
        with patch.object(context_processors.System_Settings.objects, "get") as settings_get, patch.object(context_processors, "get_os_banner") as promo, patch.object(context_processors, "should_show_github_star_prompt") as star:
            settings_get.return_value.read_only_mode = True
            context = context_processors.globalize_vars(request)
        promo.assert_not_called()
        star.assert_not_called()
        self.assertFalse(context["SHOW_PLG_LINK"])
        self.assertFalse(context["SHOW_GITHUB_STAR_PROMPT"])
        self.assertEqual(context["additional_banners"][0]["source"], "read_only_mode")

    @override_settings(ASPM_GIT_SHA="a" * 40)
    def test_standalone_report_has_version_without_request_context(self):
        html = render_to_string("dojo/custom_html_report.html", {"report_name": "Release validation", "widgets": []})
        self.assertIn("ASPM 1.0.1 rc1", html)
        self.assertIn("DefectDojo OSS 3.5.100", html)
        self.assertIn("a" * 40, html)
        self.assertNotIn("fonts.googleapis.com", html)

    @override_settings(ASPM_SHOW_UPSTREAM_PROMOTIONS=False)
    def test_error_promos_are_not_stored_but_api_error_contract_is_preserved(self):
        request = RequestFactory().get("/finding/1")
        request.session = {}
        ErrorPageProductAnnouncement(request=request)
        self.assertNotIn("_product_banners", request.session)
        data = {"detail": "Permission denied"}
        ErrorPageProductAnnouncement(response_data=data)
        self.assertEqual(data["detail"], "Permission denied")
        self.assertEqual(len(data["pro"]), 1)

    @override_settings(ASPM_SHOW_UPSTREAM_PROMOTIONS=False)
    def test_old_promos_are_consumed_without_removing_operator_banners(self):
        request = RequestFactory().get("/")
        request.session = {"_product_banners": [{"source": "product_announcement", "message": "Old promo"}, {"source": "operator", "message": "Maintenance"}]}
        with patch.object(context_processors.System_Settings.objects, "get") as settings_get:
            settings_get.return_value.read_only_mode = False
            context = context_processors.globalize_vars(request)
        self.assertEqual(context["additional_banners"], [{"source": "operator", "message": "Maintenance"}])
        self.assertNotIn("_product_banners", request.session)
