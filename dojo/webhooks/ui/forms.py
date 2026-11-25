from django import forms
from django.core.exceptions import ValidationError

from dojo.models import Product
from dojo.webhooks.catalog import EVENT_TYPES
from dojo.webhooks.validation import validate_endpoint, validate_rules


class SubscriptionForm(forms.Form):
    name = forms.CharField(max_length=120)
    product_id = forms.IntegerField(min_value=1, label="Project ID", help_text="Use the numeric ID from Project details. Product scope cannot change after creation.")
    endpoint = forms.URLField(max_length=1000, validators=[validate_endpoint], help_text="Public HTTPS on port 443. Redirects, credentials and query strings are rejected.")
    enabled = forms.BooleanField(required=False, initial=True)
    events = forms.MultipleChoiceField(choices=[(value, value) for value in EVENT_TYPES if value != "webhook.test"], widget=forms.CheckboxSelectMultiple)
    repository_id = forms.CharField(required=False, label="Repository IDs", help_text="Comma-separated IDs belonging to this Project. Empty means any.")
    scanner = forms.CharField(required=False, label="Scanner types", help_text="Exact scanner names, separated by commas. Empty means any.")
    severity = forms.MultipleChoiceField(required=False, choices=[(s, s) for s in ["Critical", "High", "Medium", "Low", "Info"]], widget=forms.CheckboxSelectMultiple)
    finding_status = forms.MultipleChoiceField(required=False, choices=[(s, s.replace("_", " ")) for s in ["active", "mitigated", "false_positive", "duplicate", "out_of_scope", "inactive"]], widget=forms.CheckboxSelectMultiple)
    source = forms.MultipleChoiceField(required=False, choices=[("api", "API ingestion"), ("live", "Live finding change")], widget=forms.CheckboxSelectMultiple)
    pipeline_id = forms.CharField(required=False, label="Pipeline IDs", help_text="Exact IDs, separated by commas. Filters on missing attributes do not match.")
    timeout_seconds = forms.IntegerField(min_value=1, max_value=30, initial=5, label="HTTP timeout (seconds)")
    max_attempts = forms.IntegerField(min_value=1, max_value=12, initial=6, label="Attempts per delivery/replay")
    rate_per_minute = forms.IntegerField(min_value=1, max_value=600, initial=60, label="Maximum requests per minute")

    def clean(self):
        data = super().clean()
        try:
            data["product"] = Product.objects.get(pk=data.get("product_id"))
        except (Product.DoesNotExist, ValueError, TypeError):
            self.add_error("product_id", "Unknown Project.")
        filters = {}
        for field in ("repository_id", "scanner", "severity", "finding_status", "source", "pipeline_id"):
            values = data.get(field)
            if isinstance(values, str):
                values = [value.strip() for value in values.split(",") if value.strip()]
            if values:
                filters[field] = list(dict.fromkeys(values))
        data["filters"] = filters
        if data.get("events"):
            try:
                validate_rules(data["events"], filters)
            except ValidationError as error:
                raise forms.ValidationError(error.messages) from error
        return data

    @classmethod
    def for_subscription(cls, subscription, data=None):
        initial = {field: getattr(subscription, field) for field in ("name", "product_id", "endpoint", "enabled", "events", "timeout_seconds", "max_attempts", "rate_per_minute")}
        for field, values in subscription.filters.items():
            initial[field] = ", ".join(values) if field in {"repository_id", "scanner", "pipeline_id"} else values
        return cls(data=data, initial=initial)
