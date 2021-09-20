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
from testfixtures import StringComparison

from webwhois.exceptions import _DEPRECATED_MSG, WebwhoisError


class WebwhoisErrorTest(SimpleTestCase):
    def test_getitem(self):
        data = (
            # error, key, value
            (WebwhoisError(code=sentinel.code, title=sentinel.title), 'code', sentinel.code),
            (WebwhoisError(code=sentinel.code, title=sentinel.title), 'title', sentinel.title),
            (WebwhoisError(code=sentinel.code, title=sentinel.title), 'message', None),
            (WebwhoisError(code=sentinel.code, title=sentinel.title, message=sentinel.message),
             'message', sentinel.message),
            (WebwhoisError(code=sentinel.code, title=sentinel.title, another=sentinel.value),
             'another', sentinel.value),
        )
        for error, key, value in data:
            with self.subTest(key=key):
                with warnings.catch_warnings(record=True) as captured:
                    warnings.simplefilter("always")
                    self.assertEqual(error[key], value)

                warns = [i.message for i in captured]
                self.assertEqual(len(warns), 1)
                self.assertIsInstance(warns[0], DeprecationWarning)
                self.assertEqual(cast(DeprecationWarning, warns[0]).args,
                                 (StringComparison('.*server_exception.*is deprecated.*'), ))

    def test_getitem_error(self):
        error = WebwhoisError(code=sentinel.code, title=sentinel.title)
        with self.assertRaisesRegex(KeyError, 'unknown'):
            error['unknown']

    def test_get(self):
        data = (
            # error, key, value
            (WebwhoisError(code=sentinel.code, title=sentinel.title), 'code', sentinel.code),
            (WebwhoisError(code=sentinel.code, title=sentinel.title), 'title', sentinel.title),
            (WebwhoisError(code=sentinel.code, title=sentinel.title), 'message', None),
            (WebwhoisError(code=sentinel.code, title=sentinel.title, message=sentinel.message),
             'message', sentinel.message),
            (WebwhoisError(code=sentinel.code, title=sentinel.title, another=sentinel.value),
             'another', sentinel.value),
            (WebwhoisError(code=sentinel.code, title=sentinel.title, another=sentinel.value),
             'unknown', None),
        )
        for error, key, value in data:
            with self.subTest(key=key):
                with warnings.catch_warnings(record=True) as captured:
                    warnings.simplefilter("always")
                    self.assertEqual(error.get(key), value)

                warns = [i.message for i in captured]
                self.assertEqual(len(warns), 1)
                self.assertIsInstance(warns[0], DeprecationWarning)
                self.assertEqual((_DEPRECATED_MSG, ), cast(DeprecationWarning, warns[0]).args)

    def test_get_default(self):
        error = WebwhoisError(code=sentinel.code, title=sentinel.title)
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            self.assertEqual(error.get('unknown', sentinel.default), sentinel.default)

        warns = [i.message for i in captured]
        self.assertEqual(len(warns), 1)
        self.assertIsInstance(warns[0], DeprecationWarning)
        self.assertEqual((_DEPRECATED_MSG, ), cast(DeprecationWarning, warns[0]).args)
