#
# Copyright (C) 2015-2022  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.
"""Fields used in webwhois.

Contains DeliveryField which is ChoiceWidget with other option (as EmailField). This field using DeliveryWidget with
its template and customization of validation required fields (EmailField can be required=false)
"""
from typing import Iterable

from django import forms
from django.utils.translation import gettext_lazy as _

from webwhois.constants import SEND_TO_CUSTOM, SEND_TO_IN_REGISTRY
from webwhois.forms.widgets import DeliveryType, DeliveryWidget, PlainRadioSelect


class DeliveryField(forms.MultiValueField):
    """MultiField with ChoiceField and EmailField as the other option."""

    def __init__(self, choices: Iterable[Iterable[str]], *args, **kwargs):
        fields = (forms.ChoiceField(choices=choices, widget=PlainRadioSelect, required=True),
                  forms.EmailField(required=False))
        self.widget = DeliveryWidget(widgets=[f.widget for f in fields])
        super(DeliveryField, self).__init__(fields=fields, require_all_fields=False, *args, **kwargs)

    def compress(self, data_list: Iterable) -> DeliveryType:
        """Return the ChoiceField value and CharField value."""
        return DeliveryType(*data_list)

    def validate(self, value: DeliveryType):
        if value.choice == SEND_TO_IN_REGISTRY:
            if value.custom_email:
                raise forms.ValidationError(_(
                    'Option "Send to email in registry" is incompatible with custom email. Please choose one of '
                    'the two options.'), code='unexpected_custom_email')
        elif value.choice == SEND_TO_CUSTOM:
            if not value.custom_email:
                raise forms.ValidationError(_('Custom email is required as "Send to custom email" option is selected.'
                                              ' Please fill it in.'), code='custom_email_missing')
