from __future__ import unicode_literals

from shutil import rmtree
from tempfile import mkdtemp

from fred_idl.Registry import Date, DateTime
from fred_idl.Registry.Whois import KeySet
from mock import sentinel

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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


def prepare_mkdtemp(case):
    """Create temporary directory and returns its name."""
    dirname = mkdtemp()
    case.addCleanup(rmtree, dirname)
    return dirname


def make_keyset(statuses=None):
    """Return a key set object."""
    return KeySet(handle=sentinel.handle, dns_keys=[], tech_contact_handles=[], registrar_handle=sentinel.registrar,
                  created=DateTime(Date(1, 1, 1970), 0, 0, 0), changed=None, last_transfer=None,
                  statuses=(statuses or []))
