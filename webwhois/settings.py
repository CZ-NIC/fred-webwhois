from __future__ import unicode_literals

import os
from functools import partial

from appsettings import AppSettings, StringSetting
from django.conf import settings


def _get_logger_defalt(setting_name):
    return getattr(WEBWHOIS_SETTINGS, setting_name)


class WebwhoisAppSettings(AppSettings):
    """Web whois settings."""

    CORBA_NETLOC = StringSetting(default=partial(os.environ.get, 'FRED_WEBWHOIS_NETLOC', 'localhost'))
    CORBA_CONTEXT = StringSetting(default='fred')
    LOGGER_CORBA_NETLOC = StringSetting(default=partial(_get_logger_defalt, 'CORBA_NETLOC'))
    LOGGER_CORBA_CONTEXT = StringSetting(default=partial(_get_logger_defalt, 'CORBA_CONTEXT'))

    class Meta:
        setting_prefix = 'WEBWHOIS_'


WEBWHOIS_SETTINGS = WebwhoisAppSettings()


# Webwhois settings
# Logger module. Set "pylogger.corbalogger.LoggerFailSilent" for debug or None for disable the process.
WEBWHOIS_LOGGER = getattr(settings, 'WEBWHOIS_LOGGER', 'pylogger.corbalogger.Logger')

WEBWHOIS_DNSSEC_URL = getattr(settings, 'WEBWHOIS_DNSSEC_URL', None)

# Groups names that will be displayed with/without certifications.
WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED = getattr(settings, 'WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED', [])
WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED = getattr(settings, 'WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED', [])
