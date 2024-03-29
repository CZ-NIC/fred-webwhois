#
# Copyright (C) 2022  CZ.NIC, z. s. p. o.
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
from unittest.mock import call, patch

from django.apps import apps
from django.apps.registry import Apps
from django.test import SimpleTestCase

from webwhois.constants import (LOGGER_SERVICE, PUBLIC_REQUESTS_LOGGER_SERVICE, LogEntryType, LogResult,
                                PublicRequestsLogEntryType, PublicRequestsLogResult)


class WebwhoisAppConfigTest(SimpleTestCase):
    def tearDown(self):
        apps.clear_cache()

    def test_ready(self):
        with patch('webwhois.utils.corba_wrapper.LOGGER.client', autospec=True) as logger_mock:
            Apps(('webwhois.apps.WebwhoisAppConfig', ))  # Trigger `ready`.

            self.assertEqual(logger_mock.mock_calls, [
                call.register_service(LOGGER_SERVICE, handle='webwhois'),
                call.register_log_entry_types(LOGGER_SERVICE, LogEntryType),
                call.register_results(LOGGER_SERVICE, LogResult),
                call.register_service(PUBLIC_REQUESTS_LOGGER_SERVICE, handle='pubreq'),
                call.register_log_entry_types(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType),
                call.register_results(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogResult),
            ])
