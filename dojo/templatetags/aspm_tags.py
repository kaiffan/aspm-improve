"""Public release metadata for standalone exports without a request context."""
from django import template

from dojo.aspm.branding import get_branding

register = template.Library()


@register.simple_tag
def aspm_branding():
    return get_branding()
