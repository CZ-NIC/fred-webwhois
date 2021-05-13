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
"""Utilities for cdnskey processor client."""
from cdnskey_processor_api.common_types_pb2 import DnskeyAlg, DnskeyFlags
from frgal import GrpcDecoder

from ..constants import DnskeyAlgorithm, DnskeyFlag


class CdnskeyDecoder(GrpcDecoder):
    """Decoder for cdnskey client."""

    def __init__(self) -> None:
        super().__init__()
        self.set_decoder(DnskeyFlags, self._decode_dnskey_flag)
        self.set_decoder(DnskeyAlg, self._decode_dnskey_algorithm)

    def _decode_dnskey_flag(self, value: DnskeyFlags) -> DnskeyFlag:  # type: ignore[valid-type]
        return DnskeyFlag(value.value)  # type: ignore[operator, no-any-return]

    def _decode_dnskey_algorithm(self, value: DnskeyAlg) -> DnskeyAlgorithm:  # type: ignore[valid-type]
        return DnskeyAlgorithm(value.value)  # type: ignore[operator, no-any-return]
