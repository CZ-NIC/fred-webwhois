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
from django import template
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from ..constants import DnskeyAlgorithm

register = template.Library()

# https://www.iana.org/assignments/dnskey-flags/dnskey-flags.xhtml#dnskey-flags-1
#  0-6  Unassigned
#    7  ZONE
#    8  REVOKE
# 9-14  Unassigned
#   15  Secure Entry Point (SEP)

DNSKEY_FLAG_LABELS = {
    # 0123456789ABCDEF
    #        78      F
    0b0000000100000000: _("ZONE"),
    0b0000000010000000: _("REVOKE"),
    0b0000000000000001: _("Secure Entry Point (SEP)"),
}


@register.filter
def dnskey_alg_label(alg_id):
    """Show translated description of DNSKey alg type."""
    return DnskeyAlgorithm(alg_id).label  # type: ignore[operator]


@register.filter
def dnskey_flag_labels(flags):
    """Show DNSKey flag descriptions."""
    if not (0 <= flags <= 0xffff):
        raise ValueError("dnskey_flag_labels: flags %d is out of range." % flags)

    descriptions = []
    for mask, label in DNSKEY_FLAG_LABELS.items():
        if flags & mask:
            descriptions.append(force_text(label))
    return ", ".join(descriptions)
