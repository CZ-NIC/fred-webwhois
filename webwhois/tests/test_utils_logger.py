#
# Copyright (C) 2016-2020  CZ.NIC, z. s. p. o.
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

from __future__ import unicode_literals

from unittest.mock import MagicMock, call

from django.test import SimpleTestCase
from pylogger.corbalogger import Logger

from webwhois.utils.logger import create_logger


class TestLogger(SimpleTestCase):

    def test_create_logger(self):
        with self.assertRaisesRegexp(ImportError, "foo doesn't look like a module path"):
            create_logger("foo", None)
        with self.assertRaisesRegexp(ImportError, "No module named '?foo'?"):
            create_logger("foo.off", None)
        with self.assertRaisesRegexp(ImportError, 'does not define a "foo" attribute/class'):
            create_logger("pylogger.foo", None)

        corba = MagicMock()
        corba.getServices.return_value = []
        response = create_logger("pylogger.corbalogger.Logger", corba)
        self.assertIsInstance(response, Logger)
        self.assertEqual(corba.mock_calls, [call.getServices()])
