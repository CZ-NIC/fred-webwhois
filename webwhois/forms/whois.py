from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

from .fields import RemoveWhitespacesField


class WhoisForm(forms.Form):
    "Whois form to enter HANDLE."

    handle = RemoveWhitespacesField(label=_("Domain (without www.) / Handle"), required=True,
                                    validators=[RegexValidator("^[\w_.:-]{1,255}$")])
