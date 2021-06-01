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
from django.test import SimpleTestCase

from webwhois.constants import DnskeyAlgorithm, DnskeyFlag


class DnskeyAlgorithmTest(SimpleTestCase):
    def test_props(self):
        self.assertEqual(DnskeyAlgorithm.DELETE_DS.name, 'DELETE_DS')
        self.assertEqual(DnskeyAlgorithm.DELETE_DS.value, 0)
        self.assertEqual(DnskeyAlgorithm.DELETE_DS.label, 'Delete DS')


class DnskeyFlagTest(SimpleTestCase):
    def test_props(self):
        self.assertEqual(DnskeyFlag.ZONE.name, 'ZONE')
        self.assertEqual(DnskeyFlag.ZONE.value, 256)
        self.assertEqual(DnskeyFlag.ZONE.label, 'ZONE')

    def test_flags(self):
        dnskey = DnskeyFlag.ZONE | DnskeyFlag.REVOKE | DnskeyFlag.UNASSIGNED_2
        flags = dnskey.flags  # type: ignore[attr-defined]
        self.assertEqual(flags, {DnskeyFlag.ZONE, DnskeyFlag.REVOKE, DnskeyFlag.UNASSIGNED_2})
