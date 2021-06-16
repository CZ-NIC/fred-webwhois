#
# Copyright (C) 2018-2021  CZ.NIC, z. s. p. o.
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
"""Webwhois constants."""
from enum import Enum, unique

from django.utils.translation import ugettext_lazy as _

from .utils import _DnskeyAlgorithmBase, _DnskeyFlagBase

STATUS_LINKED = 'linked'
STATUS_DELETE_CANDIDATE = 'deleteCandidate'

STATUS_VERIFICATION_IN_PROCESS = 'contactInManualVerification'
STATUS_VERIFICATION_PASSED = 'contactPassedManualVerification'
STATUS_VERIFICATION_FAILED = 'contactFailedManualVerification'

STATUS_CONDITIONALLY_IDENTIFIED = 'conditionallyIdentifiedContact'
STATUS_IDENTIFIED = 'identifiedContact'
STATUS_VALIDATED = 'validatedContact'

SEND_TO_IN_REGISTRY = 'email_in_registry'
SEND_TO_CUSTOM = 'custom_email'


# https://www.iana.org/assignments/dns-sec-alg-numbers/dns-sec-alg-numbers.xhtml
_DNSKEY_ALGORITHMS = {
    'DELETE_DS': (0, _("Delete DS")),
    'RSAMD5': (1, _("RSA/MD5 (deprecated, see 5)")),
    'DH': (2, _("Diffie-Helman")),
    'DSA': (3, _("DSA/SHA1")),
    'RSASHA1': (5, _("RSA/SHA-1")),
    'DSA_NSEC3_SHA1': (6, _("DSA-NSEC3-SHA1")),
    'RSASHA1_NSEC3_SHA1': (7, _("RSASHA1-NSEC3-SHA1")),
    'RSASHA256': (8, _("RSA/SHA-256")),
    'RSASHA512': (10, _("RSA/SHA-512")),
    'GOST': (12, _("GOST R 34.10-2001")),
    'ECDSAP256SHA256': (13, _("ECDSA Curve P-256 with SHA-256")),
    'ECDSAP384SHA384': (14, _("ECDSA Curve P-384 with SHA-384")),
    'ED25519': (15, _("Ed25519")),
    'ED448': (16, _("Ed448")),
    'INDIRECT': (252, _("Reserved for Indirect Keys")),
    'PRIVATEDNS': (253, _("Private algorithm")),
    'PRIVATEOID': (254, _("Private algorithm OID")),
}
# Add usassigned
_DNSKEY_ALGORITHMS.update({'UNASSIGNED_{}'.format(i): (i, _("Unassigned")) for i in range(17, 123)})
# Add reserved
_DNSKEY_ALGORITHMS.update({'RESERVED_{}'.format(i): (i, _("Reserved")) for i in range(0, 256)
                           if i not in [v[0] for v in _DNSKEY_ALGORITHMS.values()]})
DnskeyAlgorithm = _DnskeyAlgorithmBase('DnskeyAlgorithm', _DNSKEY_ALGORITHMS)  # type: ignore[arg-type]


# https://www.iana.org/assignments/dnskey-flags/dnskey-flags.xhtml
_DNSKEY_FLAGS = {
    'ZONE': (1 << 8, _("ZONE")),
    'REVOKE': (1 << 7, _("REVOKE")),
    'SECURE_ENTRY_POINT': (1 << 0, _("Secure Entry Point (SEP)")),
}
# Add usassigned
_DNSKEY_FLAGS.update({'UNASSIGNED_{}'.format(15 - i): (1 << i, _("Unassigned")) for i in range(0, 16)
                      if 1 << i not in [v[0] for v in _DNSKEY_FLAGS.values()]})
DnskeyFlag = _DnskeyFlagBase('DnskeyFlag', _DNSKEY_FLAGS)  # type: ignore[arg-type]


@unique
class CdnskeyStatus(str, Enum):
    """Enum with cdnskey scan status."""

    INSECURE_KEY = ('INSECURE_KEY', _('Key for insecure domain is present.'))
    INSECURE_EMPTY = ('INSECURE_EMPTY', _('Key for insecure domain is not present.'))
    SECURE_KEY = ('SECURE_KEY', _('Key for secure domain is present.'))
    SECURE_EMPTY = ('SECURE_EMPTY', _('Key for secure domain is not present.'))
    UNTRUSTWORTHY = ('UNTRUSTWORTHY', _('Unable to verify CDNSKEY record.'))
    UNKNOWN = ('UNKNOWN', _('No information about domain is available.'))
    UNRESOLVED = ('UNRESOLVED', _('No information about insecure domain is available at the nameserver.'))
    UNRESOLVED_IP = ('UNRESOLVED_IP', _('Unable to resolve IP address of the nameserver.'))

    label: str

    def __new__(cls, value: str, label: str):
        """Construct item with label."""
        obj = super().__new__(cls, value)
        obj._value_ = value

        obj.label = label
        return obj
