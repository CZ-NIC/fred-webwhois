import idna
from django import forms
from django.core.validators import MaxLengthValidator
from django.utils.translation import ugettext_lazy as _

from .fields import RemoveWhitespacesField


class WhoisForm(forms.Form):
    "Whois form to enter HANDLE."

    handle = RemoveWhitespacesField(label=_("Domain (without www. prefix) / Handle"), required=True,
                                    validators=[MaxLengthValidator(255)])
