#!/usr/bin/python
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
from unittest.mock import call, patch, sentinel

from django.test import SimpleTestCase

from webwhois.context_processors import _get_managed_zones, managed_zones
from webwhois.utils import WHOIS


class ManagedZonesTest(SimpleTestCase):
    def setUp(self):
        spec = ('get_managed_zone_list', )
        patcher = patch.object(WHOIS, 'client', spec=spec)
        self.addCleanup(patcher.stop)
        patcher.start()

        WHOIS.get_managed_zone_list.return_value = [sentinel.zone]
        _get_managed_zones.cache_clear()

    def test_processor(self):
        zones = managed_zones(sentinel.request)

        self.assertEqual(zones, {'managed_zones': (sentinel.zone, )})
        self.assertEqual(WHOIS.mock_calls, [call.get_managed_zone_list()])

    def test_cached(self):
        zones_1 = managed_zones(sentinel.request)
        zones_2 = managed_zones(sentinel.request)

        self.assertEqual(zones_1, {'managed_zones': (sentinel.zone, )})
        self.assertEqual(zones_2, {'managed_zones': (sentinel.zone, )})
        # Only one call to backend was made.
        self.assertEqual(WHOIS.mock_calls, [call.get_managed_zone_list()])
