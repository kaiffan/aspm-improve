from django import forms
from django.utils.translation import gettext_lazy as _

COMPARISON_CATEGORIES = (("new", _("New")), ("fixed", _("Fixed")), ("unchanged", _("Unchanged")))
MAX_ID = 2**63 - 1


class CompareCommitsForm(forms.Form):
    base = forms.IntegerField(min_value=1, max_value=MAX_ID)
    category = forms.ChoiceField(choices=COMPARISON_CATEGORIES, required=False)
    after = forms.IntegerField(min_value=1, max_value=MAX_ID, required=False)
