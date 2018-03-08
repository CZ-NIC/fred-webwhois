from __future__ import unicode_literals

import os
from functools import partial

from appsettings import AppSettings, StringSetting
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


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

WEBWHOIS_SEARCH_ENGINES = getattr(settings, 'WEBWHOIS_SEARCH_ENGINES', (
    {"label": "WHOIS.COM Lookup", "href": "http://www.whois.com/whois/"},
    {"label": "IANA WHOIS Service", "href": "http://www.iana.org/whois"},
))
for dct in WEBWHOIS_SEARCH_ENGINES:
    if not (dct.get("href") and dct.get("label")):
        raise ImproperlyConfigured("WEBWHOIS_SEARCH_ENGINES value %s does not have required keys." % dct)

WEBWHOIS_HOW_TO_REGISTER_LINK = dct = getattr(settings, 'WEBWHOIS_HOW_TO_REGISTER_LINK', None)
if dct and not (dct.get("href") and dct.get("label")):
    raise ImproperlyConfigured("WEBWHOIS_HOW_TO_REGISTER_LINK value %s does not have required keys." % dct)


# Groups names that will be displayed with/without certifications.
WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED = getattr(settings, 'WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED', [])
WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED = getattr(settings, 'WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED', [])
