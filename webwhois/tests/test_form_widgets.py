#
# Copyright (C) 2020  CZ.NIC, z. s. p. o.
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

from django import forms
from django.test import SimpleTestCase

from webwhois.forms.public_request import DeliveryType
from webwhois.forms.widgets import DeliveryWidget


class TestDeliveryWidget(SimpleTestCase):
    """Test widgets from widgets module"""

    def test_decompress(self):
        widget = DeliveryWidget(widgets=[])
        empty = widget.decompress(None)
        self.assertEqual(empty, [None, None])

        val = widget.decompress(DeliveryType("custom_email", "foo@foo.test"))
        self.assertEqual(val, ["custom_email", "foo@foo.test"])

    def test_overriding_required(self):
        fields = (forms.ChoiceField(choices=(('1', '1'), ('2', '2')), required=True),
                  forms.EmailField(required=False))
        widget = DeliveryWidget(widgets=[f.widget for f in fields])
        context = widget.get_context('send_to', DeliveryType('1', '2'), {'required': True, 'id': 'id_send_to'})
        self.assertEqual(context['widget']['subwidgets'][1]['attrs']['required'], False)
