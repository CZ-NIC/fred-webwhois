#
# Copyright (C) 2021  CZ.NIC, z. s. p. o.
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
#
import warnings
from typing import cast
from unittest.mock import sentinel

from django.test import SimpleTestCase

from webwhois.utils.deprecation import deprecated_context


class DeprecatedContextTest(SimpleTestCase):
    def test_deprecated(self):
        deprecated = deprecated_context(sentinel.value, sentinel.message)

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")

            self.assertEqual(deprecated, sentinel.value)

        warns = [i.message for i in captured]
        self.assertEqual(len(warns), 1)
        self.assertIsInstance(warns[0], DeprecationWarning)
        self.assertEqual(cast(DeprecationWarning, warns[0]).args, (sentinel.message, ))
