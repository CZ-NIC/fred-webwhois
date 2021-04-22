"""Settings of Webwhois project"""
import logging
import os
import socket
import sys
from email.utils import getaddresses
from http import HTTPStatus

import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

env = environ.Env()

###############################################################################
# Basic settings
SECRET_KEY = env.str('SECRET_KEY')

ADMINS = getaddresses([env.str('ADMINS', default='')])

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

DEBUG = env.bool('DEBUG', default=False)

###############################################################################
# Application
INSTALLED_APPS = [
    'django.contrib.staticfiles.apps.StaticFilesConfig',
    'webwhois.apps.WebwhoisAppConfig',
]

CACHES = {"default": env.cache("CACHE_URL", default='locmemcache://')}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'webwhois_urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        # Enable templates from application directories (default is False).
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.csrf',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
            ],
        },
    },
]

###############################################################################
# Email settings
#
# Only for error emails.
if 'EMAIL_HOST' in env:
    EMAIL_HOST = env.str('EMAIL_HOST')
if 'EMAIL_HOST_USER' in env:
    EMAIL_HOST_USER = env.str('EMAIL_HOST_USER')
if 'EMAIL_HOST_PASSWORD' in env:
    EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')
if 'EMAIL_PORT' in env:
    EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_SUBJECT_PREFIX = '[webwhois@{}]: '.format(env.str('ENVIRONMENT', default=socket.gethostname()))
SERVER_EMAIL = env.str('SERVER_EMAIL',
                       default='webwhois@{}'.format(env.str('ENVIRONMENT', default=socket.gethostname())))

###############################################################################
# Static files

STATIC_ROOT = '/var/www/static/'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    # Webwhois still uses jQuery from django admin.
    '/app/venv/lib/python' + sys.version[:3] + '/site-packages/django/contrib/admin/static/'
]

###############################################################################
# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True

# CSRF
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True

###############################################################################
# Webwhois specific settings can be set in environment.
# See django-appsettings on how envirnment variables are handled.

###############################################################################
# Locale settings
USE_TZ = True
TIME_ZONE = env.str('TIME_ZONE', default='UTC')


###############################################################################
# Logging
#
# Log are printed to stdout, to be processed by docker.
def skip_not_implemented(record: logging.LogRecord):
    """Skip records triggered by 'Not Implemented' HTTP status."""
    return getattr(record, 'status_code', None) != HTTPStatus.NOT_IMPLEMENTED


def skip_disallowed_host(record: logging.LogRecord):
    """Skip records triggered by DisallowedHost."""
    return record.name != 'django.security.DisallowedHost'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'skip_not_implemented': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_not_implemented,
        },
        'skip_disallowed_host': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_disallowed_host,
        },
    },
    'formatters': {
        'verbose': {'format': '%(asctime)s %(levelname)-8s %(module)s:%(funcName)s:%(lineno)s %(message)s'},
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['skip_not_implemented', 'skip_disallowed_host'],
            'include_html': True,
        },
        'stdout': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['stdout', 'mail_admins'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        # Override django logger to only propagate logs to root logger.
        'django': {
            'propagate': True,
        },
    },
}

# Configure Sentry
if 'SENTRY_DSN' in env:
    sentry_sdk.init(
        dsn=env.str('SENTRY_DSN'),
        environment=env.str('ENVIRONMENT', default=None),
        integrations=[DjangoIntegration()],
        send_default_pii=True,
        ca_certs=env.str('SENTRY_CA_CERTS', default=None),
    )
    ignore_logger("django.security.DisallowedHost")
