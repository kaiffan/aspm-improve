from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from dojo.utils import add_breadcrumb
from dojo.webhooks.models import WebhookDelivery, WebhookSubscription
from dojo.webhooks.services import (
    change_subscription,
    replay_delivery,
    require_manager,
    save_subscription,
    test_event,
    validate_configuration,
)
from dojo.webhooks.ui.forms import SubscriptionForm


def manager_only(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not settings.ASPM_WEBHOOKS_ENABLED:
            raise Http404
        require_manager(request.user)
        add_breadcrumb(title="Webhooks", url=reverse("aspm_webhooks"), request=request)
        response = view(request, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        response["Referrer-Policy"] = "same-origin"
        return response
    return wrapped


@manager_only
@require_http_methods(["GET"])
def subscriptions(request):
    rows = WebhookSubscription.objects.filter(archived=False).select_related("product").defer("encrypted_secret")
    query = request.GET.get("q", "")[:120]
    if query:
        rows = rows.filter(name__icontains=query)
    page = Paginator(rows.order_by("-pk"), 25).get_page(request.GET.get("page"))
    return render(request, "dojo/webhooks/list.html", {"page": page, "query": query})


@manager_only
@require_http_methods(["GET", "POST"])
def edit(request, pk=None):
    subscription = get_object_or_404(WebhookSubscription.objects.defer("encrypted_secret"), pk=pk, archived=False) if pk else None
    data = request.POST if request.method == "POST" else None
    form = SubscriptionForm.for_subscription(subscription, data) if subscription else SubscriptionForm(data=data)
    if request.method == "POST" and form.is_valid():
        if request.POST.get("intent") == "validate":
            try:
                validate_configuration(actor=request.user, values=form.cleaned_data, subscription=subscription)
            except ValidationError as error:
                form.add_error(None, error)
            else:
                messages.success(request, "Configuration is valid. No HTTP request has been sent.")
            return render(request, "dojo/webhooks/form.html", {"form": form, "subscription": subscription})
        try:
            subscription, raw = save_subscription(actor=request.user, values=form.cleaned_data, subscription=subscription)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Webhook saved. Configuration changes revoke pending deliveries from the previous revision.")
            if raw:
                return render(request, "dojo/webhooks/secret.html", {"subscription": subscription, "one_time_secret": raw})
            return redirect("aspm_webhook_history", pk=subscription.pk)
    return render(request, "dojo/webhooks/form.html", {"form": form, "subscription": subscription})


@manager_only
@require_http_methods(["GET"])
def history(request, pk):
    subscription = get_object_or_404(WebhookSubscription.objects.defer("encrypted_secret"), pk=pk)
    rows = WebhookDelivery.objects.filter(subscription=subscription).select_related("event").defer("event__payload", "event__subscribers").order_by("-created_at")
    state = request.GET.get("state", "")
    if state in WebhookDelivery.State.values:
        rows = rows.filter(state=state)
    return render(request, "dojo/webhooks/history.html", {"subscription": subscription, "page": Paginator(rows, 25).get_page(request.GET.get("page")), "states": WebhookDelivery.State.values, "selected_state": state})


@manager_only
@require_http_methods(["GET"])
def attempts(request, pk, delivery_id):
    delivery = get_object_or_404(WebhookDelivery.objects.select_related("event", "subscription").defer("subscription__encrypted_secret", "event__payload", "event__subscribers"), pk=delivery_id, subscription_id=pk)
    page = Paginator(delivery.history.order_by("-number"), 25).get_page(request.GET.get("page"))
    return render(request, "dojo/webhooks/attempts.html", {"delivery": delivery, "page": page})


@manager_only
@require_POST
def action(request, pk, action):
    subscription = get_object_or_404(WebhookSubscription.objects.defer("encrypted_secret"), pk=pk, archived=False)
    try:
        if action == "test":
            test_event(subscription, request.user)
            raw = None
        else:
            raw = change_subscription(subscription, request.user, action)
    except (ValidationError, WebhookSubscription.DoesNotExist):
        return HttpResponseBadRequest("Action unavailable. Check that the subscription is enabled and its configuration is valid.")
    if raw:
        return render(request, "dojo/webhooks/secret.html", {"subscription": subscription, "one_time_secret": raw})
    messages.success(request, "Webhook action recorded. Test events are delivered asynchronously.")
    return redirect("aspm_webhooks" if action == "archive" else "aspm_webhook_history", **({} if action == "archive" else {"pk": pk}))


@manager_only
@require_POST
def replay(request, pk, delivery_id):
    row = get_object_or_404(WebhookDelivery, pk=delivery_id, subscription_id=pk)
    try:
        replay_delivery(row, request.user)
    except ValidationError:
        return HttpResponseBadRequest("Replay requires an enabled subscription and a terminal delivery.")
    messages.success(request, "Replay queued with the original event ID. Previous attempts remain in history.")
    return redirect("aspm_webhook_history", pk=pk)
