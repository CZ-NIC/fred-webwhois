import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Webwhois settings

# CORBA CONFIGURATION
WEBWHOIS_CORBA_IOR = getattr(settings, 'WEBWHOIS_CORBA_IOR', os.environ.get('FRED_WEBWHOIS_IOR', 'localhost'))
WEBWHOIS_CORBA_CONTEXT = getattr(settings, 'WEBWHOIS_CORBA_CONTEXT', 'fred')

# Logger module. Set "pylogger.corbalogger.LoggerFailSilent" for debug or None for disable the process.
WEBWHOIS_LOGGER = getattr(settings, 'WEBWHOIS_LOGGER', 'pylogger.corbalogger.Logger')
WEBWHOIS_LOGGER_CORBA_IOR = WEBWHOIS_CORBA_IOR
WEBWHOIS_LOGGER_CORBA_CONTEXT = WEBWHOIS_CORBA_CONTEXT

WEBWHOIS_DNSSEC_URL = getattr(settings, 'WEBWHOIS_DNSSEC_URL', None)

WEBWHOIS_SEARCH_ENGINES = getattr(settings, 'WEBWHOIS_SEARCH_ENGINES', (
    {"label": "WHOIS.COM Lookup", "href": "http://www.whois.com/whois/"},
    {"label": "IANA WHOIS Service", "href": "http://www.iana.org/whois"},
))
for dct in WEBWHOIS_SEARCH_ENGINES:
    if not (dct.get("href") and dct.get("label")):
        raise ImproperlyConfigured("WEBWHOIS_SEARCH_ENGINES value %s does not have required keys." % dct)

# Mojeid urls configuration
WEBWHOIS_MOJEID_REGISTRY_ENDPOINT = getattr(settings, 'WEBWHOIS_MOJEID_REGISTRY_ENDPOINT', None)
WEBWHOIS_MOJEID_TRANSFER_ENDPOINT = getattr(settings, 'WEBWHOIS_MOJEID_TRANSFER_ENDPOINT', None)
WEBWHOIS_MOJEID_LINK_WHY = getattr(settings, 'WEBWHOIS_MOJEID_LINK_WHY', None)

# WebWhois - List of Registrars:
WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL = getattr(settings, 'WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL', None)
WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL = getattr(settings, 'WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL', None)
WEBWHOIS_REGISTRAR_SUPPORTS_DNSSEC = getattr(settings, 'WEBWHOIS_REGISTRAR_SUPPORTS_DNSSEC', None)
WEBWHOIS_REGISTRAR_SUPPORTS_MOJEID = getattr(settings, 'WEBWHOIS_REGISTRAR_SUPPORTS_MOJEID', None)
WEBWHOIS_REGISTRAR_SUPPORTS_IPV6 = getattr(settings, 'WEBWHOIS_REGISTRAR_SUPPORTS_IPV6', None)

# Storage for files of dobradomena.

# /tmp/dobradomena/fred_a/en/manual.pdf
WEBWHOIS_DOBRADOMENA_ROOT = getattr(settings, 'WEBWHOIS_DOBRADOMENA_ROOT', None)
WEBWHOIS_DOBRADOMENA_FILE_NAME = getattr(settings, 'WEBWHOIS_DOBRADOMENA_FILE_NAME', None)
# http://%(handle)s.dobradomena.cz/dobradomena/
WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN = getattr(settings, 'WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN', None)
WEBWHOIS_HOW_TO_REGISTER_LINK = dct = getattr(settings, 'WEBWHOIS_HOW_TO_REGISTER_LINK', None)
if dct and not (dct.get("href") and dct.get("label")):
    raise ImproperlyConfigured("WEBWHOIS_HOW_TO_REGISTER_LINK value %s does not have required keys." % dct)


# Groups names that will be displayed with/without certifications.
WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED = getattr(settings, 'WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED', [])
WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED = getattr(settings, 'WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED', [])
