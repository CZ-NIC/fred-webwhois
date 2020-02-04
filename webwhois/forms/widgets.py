#
# Copyright (C) 2019-2020  CZ.NIC, z. s. p. o.
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
"""Widgets used in webwhois.

Contains DeliveryWidget which is ChoiceWidget with other option (as EmailField).
DeliveryWidget contains template and customization of validation required fields (EmailField can be required=false)
"""

from typing import List, NamedTuple, Optional

from django import forms

DeliveryType = NamedTuple('DeliveryType', [('choice', str), ('custom_email', str)])


class PlainRadioSelect(forms.RadioSelect):
    """RadioSelect with custom template which is not rendering it as a list."""

    template_name = 'forms/widgets/widget_optional_radio_select.html'


class DeliveryWidget(forms.MultiWidget):
    """Widget for DeliveryField."""

    def decompress(self, value: Optional[DeliveryType]) -> List[Optional[str]]:
        if not value:
            return [None, None]
        return [value.choice, value.custom_email]

    def get_context(self, name, value, attrs):
        # workaround for not fully working require_all_fields in MultiValueField
        context = super().get_context(name, value, attrs)
        context['widget']['subwidgets'][1]['attrs']['required'] = False
        return context
