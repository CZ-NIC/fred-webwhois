#
# Copyright (C) 2016-2018  CZ.NIC, z. s. p. o.
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

from django.test import SimpleTestCase
from mock import MagicMock, Mock, call
from pylogger.corbalogger import Logger

from webwhois.utils.logger import create_logger


class TestLogger(SimpleTestCase):

    def test_create_logger(self):
        with self.assertRaisesRegexp(ImportError, "foo doesn't look like a module path"):
            create_logger("foo", None, None)
        with self.assertRaisesRegexp(ImportError, "No module named '?foo'?"):
            create_logger("foo.off", None, None)
        with self.assertRaisesRegexp(ImportError, 'does not define a "foo" attribute/class'):
            create_logger("pylogger.foo", None, None)

        corba, ccreg = MagicMock(), Mock()
        corba.getServices.return_value = []
        response = create_logger("pylogger.corbalogger.Logger", corba, ccreg)
        self.assertIsInstance(response, Logger)
        self.assertEqual(ccreg.mock_calls, [])
        self.assertEqual(corba.mock_calls, [call.getServices()])
