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

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from webwhois.constants import SEND_TO_CUSTOM, SEND_TO_IN_REGISTRY
from webwhois.forms.fields import DeliveryField
from webwhois.forms.public_request import DeliveryType


class TestDeliveryField(SimpleTestCase):
    """Test fields from fields module"""

    def test_compress(self):
        field = DeliveryField(choices=['1', '2'])
        compressed = field.compress([SEND_TO_CUSTOM, 'foo@foo.test'])
        self.assertEqual(compressed, DeliveryType(SEND_TO_CUSTOM, 'foo@foo.test'))

    def test_validate_redundant_email(self):
        # send to registry => empty custom email
        field = DeliveryField(choices=['1', '2'])
        self.assertRaises(ValidationError, field.validate, DeliveryType(SEND_TO_IN_REGISTRY, 'foo@foo.test'))

    def test_validate_missing_email(self):
        # send to custom => not empty custom email
        field = DeliveryField(choices=['1', '2'])
        self.assertRaises(ValidationError, field.validate, DeliveryType(SEND_TO_CUSTOM, ''))
