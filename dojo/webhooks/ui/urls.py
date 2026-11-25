from django.urls import path

from dojo.webhooks.ui import views

urlpatterns = [
    path("settings/integrations/webhooks/", views.subscriptions, name="aspm_webhooks"),
    path("settings/integrations/webhooks/new/", views.edit, name="aspm_webhook_new"),
    path("settings/integrations/webhooks/<int:pk>/edit/", views.edit, name="aspm_webhook_edit"),
    path("settings/integrations/webhooks/<int:pk>/", views.history, name="aspm_webhook_history"),
    path("settings/integrations/webhooks/<int:pk>/actions/<str:action>/", views.action, name="aspm_webhook_action"),
    path("settings/integrations/webhooks/<int:pk>/deliveries/<uuid:delivery_id>/", views.attempts, name="aspm_webhook_attempts"),
    path("settings/integrations/webhooks/<int:pk>/deliveries/<uuid:delivery_id>/replay/", views.replay, name="aspm_webhook_replay"),
]
