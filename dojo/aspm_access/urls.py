from django.urls import path

from dojo.aspm_access import views, workspace

urlpatterns = [
    path("sso/login", views.start, name="aspm_oidc_login"),
    path("sso/callback", views.callback, name="aspm_oidc_callback"),
    path("sso/logout", views.end, name="aspm_oidc_logout"),
]

urlpatterns += [
    path("workspace/classic", workspace.classic, name="aspm_classic"),
    path("workspace/projects", workspace.projects, name="aspm_projects"),
    path("workspace/reports", workspace.reports, name="aspm_reports"),
    path("workspace/scan-processing", workspace.scan_processing, name="aspm_scan_processing"),
    path("workspace/system-health", workspace.system_health, name="aspm_system_health"),
    path("workspace/scanners", workspace.scanners, name="aspm_scanners"),
    path("workspace/access", workspace.sso_mappings, name="aspm_sso_mappings"),
    path("workspace/projects/<int:product_id>/engagement-policy", workspace.engagement_policy, name="aspm_engagement_policy"),
]
