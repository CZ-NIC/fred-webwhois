#
# Copyright (C) 2015-2020  CZ.NIC, z. s. p. o.
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

import os
from unittest.mock import call, sentinel

from fred_idl.Registry import IsoDateTime
from fred_idl.Registry.Whois import KeySet, PlaceAddress, Registrar

CALL_BOOL = call.__bool__()
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(__file__), 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


def apply_patch(case, patcher):
    """
    Add patcher into cleanup, start it and return it.

    Examples:
        apply_patch(self, patch('module'))

        or in subclass of GingerAssertMixin:

        self.apply_patch(patch('module'))
        mocked = self.apply_patch(patch('module', mock))

    """
    start, stop = patcher.start, patcher.stop
    case.addCleanup(stop)
    return start()


def make_keyset(statuses=None):
    """Return a key set object."""
    return KeySet(handle=sentinel.handle, dns_keys=[], tech_contact_handles=[], registrar_handle=sentinel.registrar,
                  created=IsoDateTime('1970-01-01T00:00:00Z'), changed=None, last_transfer=None,
                  statuses=(statuses or []))


def make_address():
    return PlaceAddress(street1=sentinel.street1, street2=sentinel.street2, street3=sentinel.street3,
                        city=sentinel.city, stateorprovince=sentinel.state, postalcode=sentinel.postalcode,
                        country_code=sentinel.country_code)


def make_registrar(handle=sentinel.handle):
    """Return a registrar object."""
    return Registrar(handle=handle, name=sentinel.name, organization=sentinel.organization,
                     url=sentinel.url, phone=sentinel.phone, fax=sentinel.fax, address=make_address())
