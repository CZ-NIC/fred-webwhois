#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Django settings for webwhois project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'PUT-YOUR-SECRET-KEY-HERE'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'captcha',  # pip install django-recaptcha
    'webwhois_standalone',  # stand alone web site (outside of CZ.NIC ginger system)
    'webwhois',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)


ROOT_URLCONF = 'webwhois_site.urls'

WSGI_APPLICATION = 'webwhois_site.wsgi.application'

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/webwhois_cache',
    },
}

# Database - Project does not use database.

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', u'English'),
    ('cs', u'Česky'),
)

TIME_ZONE = 'Europe/Prague'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'


# Webwhois settings

# CORBA CONFIGURATION
WEBWHOIS_CORBA_IDL = os.environ.get('FRED_WEBWHOIS_IDL_FILE', ['/usr/share/idl/fred/Whois2.idl',
                                                               '/usr/share/idl/fred/FileManager.idl',
                                                               '/usr/share/idl/fred/Logger.idl'])
WEBWHOIS_CORBA_IOR = os.environ.get('FRED_WEBWHOIS_IOR', 'localhost')
WEBWHOIS_CORBA_CONTEXT = 'fred'

if type(WEBWHOIS_CORBA_IDL) is str:
    # Paths in environment are saved in a string separated by a space:
    # export FRED_MOJEID_IDL_FILE="path path path"
    WEBWHOIS_CORBA_IDL = WEBWHOIS_CORBA_IDL.split(" ")

# Logger module. E.g. "pylogger.corbalogger.LoggerFailSilent"
WEBWHOIS_LOGGER = None
WEBWHOIS_LOGGER_CORBA_IOR = WEBWHOIS_CORBA_IOR
WEBWHOIS_LOGGER_CORBA_CONTEXT = WEBWHOIS_CORBA_CONTEXT

WEBWHOIS_DNSSEC_URL = "http://www.nic.cz/dnssec/"  # ths can be None

WEBWHOIS_SEARCH_ENGINES = (
    {"label": "WHOIS.COM Lookup", "href": "http://www.whois.com/whois/"},
    {"label": "IANA WHOIS Service", "href": "http://www.iana.org/whois"},
)

# Mojeid urls configuration
MOJEID_HOST = os.environ.get('MOJEID_HOST', "https://mojeid.cz")
WEBWHOIS_MOJEID_REGISTRY_ENDPOINT = "%s/mogrify/preface/" % MOJEID_HOST
WEBWHOIS_MOJEID_TRANSFER_ENDPOINT = "%s/transfer/endpoint/" % MOJEID_HOST
WEBWHOIS_MOJEID_LINK_WHY = "%s/vyhody/" % MOJEID_HOST

# WebWhois - List of Registrars:
WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL = "https://www.nic.cz/page/309/how-to-become-a-registrar-/"
WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL = "https://www.nic.cz/page/928/"
WEBWHOIS_REGISTRAR_SUPPORTS_DNSSEC = "https://www.nic.cz/page/928/#dnssec"
WEBWHOIS_REGISTRAR_SUPPORTS_MOJEID = "https://www.nic.cz/page/928/#mojeid"
WEBWHOIS_REGISTRAR_SUPPORTS_IPV6 = "https://www.nic.cz/page/928/#ipv6"

# /tmp/dobradomena/fred_a/en/manual.pdf
WEBWHOIS_DOBRADOMENA_ROOT = '/tmp/dobradomena/'
WEBWHOIS_DOBRADOMENA_FILE_NAME = "manual.pdf"
# http://%(handle)s.dobradomena.cz/dobradomena/
WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN = os.environ.get('DOBRADOMENA_MANUAL', '/dobradomena/%(handle)s/%(lang)s/')
WEBWHOIS_HOW_TO_REGISTER_LINK = {
    "href": "http://www.dobradomena.cz/",
    "label": "www.dobradomena.cz"
}

# Groups names that will be displayed with/without certifications.
WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED = ["certified"]
WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED = ["uncertified"]

# Captcha configuration
WEBWHOIS_CAPTCHA_MAX_REQUESTS = 100  # Number of requests, when captcha will appear

# Load corba modules at start (if False, then it is loaded when needed).
# Environemnt variable must be set to empty string to be set to False!
LOAD_CORBA_AT_START = os.environ.get('LOAD_CORBA_AT_START', not DEBUG)

# Google Recaptcha configuration
RECAPTCHA_PUBLIC_KEY = '6Ld-fwkTAAAAAHLbjPfo5zaL4jXIOTxsRa1f_KPL'
RECAPTCHA_PRIVATE_KEY = '6Ld-fwkTAAAAAMgSLIIHkvZkOeLmllY5CU4AfBhM'
NOCAPTCHA = True  # Use google no-captcha
