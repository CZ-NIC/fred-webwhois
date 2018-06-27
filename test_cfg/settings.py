INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'webwhois.apps.WebwhoisAppConfig',
)
MIDDLEWARE = []
ROOT_URLCONF = 'webwhois.urls'
SECRET_KEY = 'SECRET'
STATIC_URL = '/static/'

WEBWHOIS_CORBA_EXPORT_MODULES = ('Registry', 'ccReg')
WEBWHOIS_LOGGER = 'pylogger.corbalogger.Logger'
WEBWHOIS_DNSSEC_URL = "http://www.nic.cz/dnssec/"  # ths can be None
WEBWHOIS_SEARCH_ENGINES = (
    {"label": "WHOIS.COM Lookup", "href": "http://www.whois.com/whois/"},
    {"label": "IANA WHOIS Service", "href": "http://www.iana.org/whois"},
)
WEBWHOIS_HOW_TO_REGISTER_LINK = {
    "href": "http://www.dobradomena.cz/",
    "label": "www.dobradomena.cz"
}
WEBWHOIS_CAPTCHA_MAX_REQUESTS = 100
