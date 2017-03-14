import os

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'webwhois',
)
ROOT_URLCONF = 'webwhois.urls'
SECRET_KEY = 'SECRET'
STATIC_URL = '/static/'

_IDL_DIR = os.environ.get('FRED_IDL_DIR', './idl/idl')
WEBWHOIS_CORBA_IDL = (os.path.join(_IDL_DIR, 'Whois2.idl'),
                      os.path.join(_IDL_DIR, 'PublicRequest.idl'),
                      os.path.join(_IDL_DIR, 'FileManager.idl'),
                      os.path.join(_IDL_DIR, 'Logger.idl'))
WEBWHOIS_CORBA_IOR = 'localhost'
WEBWHOIS_CORBA_CONTEXT = 'fred'
WEBWHOIS_CORBA_EXPORT_MODULES = ('Registry', 'ccReg')
WEBWHOIS_LOGGER = 'pylogger.corbalogger.Logger'
WEBWHOIS_LOGGER_CORBA_IOR = 'localhost'
WEBWHOIS_LOGGER_CORBA_CONTEXT = 'fred'
WEBWHOIS_DNSSEC_URL = "http://www.nic.cz/dnssec/"  # ths can be None
WEBWHOIS_SEARCH_ENGINES = (
    {"label": "WHOIS.COM Lookup", "href": "http://www.whois.com/whois/"},
    {"label": "IANA WHOIS Service", "href": "http://www.iana.org/whois"},
)
WEBWHOIS_MOJEID_REGISTRY_ENDPOINT = "http://example.cz/mogrify/preface/"
WEBWHOIS_MOJEID_TRANSFER_ENDPOINT = "http://example.cz/transfer/endpoint/"
WEBWHOIS_MOJEID_LINK_WHY = "http://example.cz/vyhody/"
WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL = "https://www.nic.cz/page/309/how-to-become-a-registrar-/"
WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL = "https://www.nic.cz/page/928/"
WEBWHOIS_REGISTRAR_SUPPORTS_DNSSEC = "https://www.nic.cz/page/928/#dnssec"
WEBWHOIS_REGISTRAR_SUPPORTS_MOJEID = "https://www.nic.cz/page/928/#mojeid"
WEBWHOIS_REGISTRAR_SUPPORTS_IPV6 = "https://www.nic.cz/page/928/#ipv6"
WEBWHOIS_DOBRADOMENA_ROOT = '/tmp/dobradomena/'
WEBWHOIS_DOBRADOMENA_FILE_NAME = "manual.pdf"
WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN = '/dobradomena/%(handle)s/%(lang)s/'
WEBWHOIS_HOW_TO_REGISTER_LINK = {
    "href": "http://www.dobradomena.cz/",
    "label": "www.dobradomena.cz"
}
WEBWHOIS_CAPTCHA_MAX_REQUESTS = 100
