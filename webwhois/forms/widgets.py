#
# Copyright (C) 2019  CZ.NIC, z. s. p. o.
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
"""
Widgets used in webwhois.

Contains DeliveryWidget which is ChoiceWidget with other option (as EmailField).
DeliveryWidget contains template and customization of validation required fields (EmailField can be required=false)
"""
from __future__ import unicode_literals

import collections

from django import forms

DeliveryType = collections.namedtuple('DeliveryType', 'choice custom_email')


class PlainRadioSelect(forms.RadioSelect):
    """RadioSelect with custom template which not rendering it as list."""
    template_name = 'forms/widgets/widget_optional_radio_select.html'


class DeliveryWidget(forms.MultiWidget):
    """Widget for DeliveryFied."""
    def decompress(self, value):
        if not value:
            return [None, None]
        return [value.choice, value.custom_email]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['subwidgets'][1]['attrs']['required'] = False
        return context
