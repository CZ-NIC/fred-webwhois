from django import forms
from django.core.validators import MaxLengthValidator
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .fields import RemoveWhitespacesField


class WhoisForm(forms.Form):
    """Whois form to enter HANDLE."""

    handle = RemoveWhitespacesField(
        label=lazy(lambda: mark_safe(_("Domain (without <em>www.</em> prefix) / Handle")), unicode)(),
        required=True, validators=[MaxLengthValidator(255)],
    )
