from __future__ import unicode_literals

import os

import six
from fred_idl.Registry import IsoDateTime
from fred_idl.Registry.Whois import KeySet
from mock import call, sentinel

if six.PY2:
    CALL_BOOL = call.__nonzero__()
else:
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

    Examples
    --------
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
