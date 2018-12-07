#
# Copyright (C) 2017-2018  CZ.NIC, z. s. p. o.
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
from __future__ import unicode_literals

from django import template
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

register = template.Library()

# https://www.iana.org/assignments/dns-sec-alg-numbers/dns-sec-alg-numbers.xhtml
DNSKEY_ALG_LABELS = {
    0: _("Delete DS"),
    1: _("RSA/MD5 (deprecated, see 5)"),
    2: _("Diffie-Helman"),
    3: _("DSA/SHA1"),
    4: _("Reserved"),
    5: _("RSA/SHA-1"),
    6: _("DSA-NSEC3-SHA1"),
    7: _("RSASHA1-NSEC3-SHA1"),
    8: _("RSA/SHA-256"),
    9: _("Reserved"),
    10: _("RSA/SHA-512"),
    11: _("Reserved"),
    12: _("GOST R 34.10-2001"),
    13: _("ECDSA Curve P-256 with SHA-256"),
    14: _("ECDSA Curve P-384 with SHA-384"),
    15: _("Ed25519"),
    16: _("Ed448"),
    252: _("Reserved for Indirect Keys"),
    253: _("Private algorithm"),
    254: _("Private algorithm OID"),
    255: _("Reserved"),
}

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
    if not (0 <= alg_id <= 255):
        raise ValueError("dnskey_alg_label: alg_id %d is out of range." % alg_id)

    if alg_id in DNSKEY_ALG_LABELS:
        return DNSKEY_ALG_LABELS[alg_id]

    if alg_id >= 17 and alg_id <= 122:
        label = _("Unassigned")
    else:
        label = _("Reserved")
    return label


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
