#
# Copyright (C) 2017-2021  CZ.NIC, z. s. p. o.
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

"""Templatetags for keyset values."""
from typing import Iterable, cast

from django import template

from ..constants import DnskeyAlgorithm, DnskeyFlag

register = template.Library()


@register.filter
def dnskey_alg_label(alg_id):
    """Show translated description of DNSKey alg type."""
    return DnskeyAlgorithm(alg_id).label  # type: ignore[operator]


@register.filter
def dnskey_flag_labels(flags):
    """Show DNSKey flag descriptions."""
    if not (0 <= flags <= sum(cast(Iterable[int], DnskeyFlag))):
        raise ValueError("dnskey_flag_labels: flags %d is out of range." % flags)

    flags = DnskeyFlag(flags)  # type: ignore[operator]
    return ", ".join(str(f.label) for f in sorted(flags.flags, reverse=True) if not f.name.startswith('UNASSIGNED'))
