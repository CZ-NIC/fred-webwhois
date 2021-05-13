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
from cdnskey_processor_api.common_types_pb2 import DnskeyAlg, DnskeyFlags
from django.test import SimpleTestCase

from webwhois.constants import DnskeyAlgorithm, DnskeyFlag
from webwhois.utils.cdnskey_client import CdnskeyDecoder


class CdnskeyDecoderTest(SimpleTestCase):
    def test_decode_flags(self):
        decoder = CdnskeyDecoder()
        data = (
            # message, result
            (DnskeyFlags(value=0), DnskeyFlag(0)),  # type: ignore[operator]
            (DnskeyFlags(value=DnskeyFlag.SECURE_ENTRY_POINT), DnskeyFlag.SECURE_ENTRY_POINT),
            (DnskeyFlags(value=DnskeyFlag.ZONE), DnskeyFlag.ZONE),
            (DnskeyFlags(value=42), DnskeyFlag(42)),  # type: ignore[operator]
        )
        for message, result in data:
            with self.subTest(message=message):
                decoded = decoder.decode(message)
                self.assertEqual(decoded, result)
                self.assertIsInstance(decoded, DnskeyFlag)

    def test_decode_algorithm(self):
        decoder = CdnskeyDecoder()
        data = (
            # message, result
            (DnskeyAlg(value=DnskeyAlgorithm.DELETE_DS), DnskeyAlgorithm.DELETE_DS),
            (DnskeyAlg(value=DnskeyAlgorithm.RSASHA512), DnskeyAlgorithm.RSASHA512),
            (DnskeyAlg(value=DnskeyAlgorithm.INDIRECT), DnskeyAlgorithm.INDIRECT),
            (DnskeyAlg(value=42), DnskeyAlgorithm(42)),  # type: ignore[operator]
        )
        for message, result in data:
            with self.subTest(message=message):
                decoded = decoder.decode(message)
                self.assertEqual(decoded, result)
                self.assertIsInstance(decoded, DnskeyAlgorithm)
