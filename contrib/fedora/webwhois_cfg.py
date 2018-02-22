#!/usr/bin/python
# -*- coding: utf-8 -*-

###############################################################################
#                  Webwhois Server Configuration File                         #
###############################################################################

# ## Django Settings ##########################################################
#
# Note: Refer to the Django documentation for a description.
SECRET_KEY = ''
DEBUG = False
ALLOWED_HOSTS = [] # fill the real hostname of the server

INSTALLED_APPS = (
    'django.contrib.staticfiles',
    'webwhois',
)

MIDDLEWARE = (
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'webwhois_urls'

STATIC_URL = '/whois_static/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
            ],
        },
    }
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '%(asctime)s - %(name)s - %(levelname)-8s - %(message)s'},
    },
    'handlers': {
        'file': {'level': 'DEBUG',
                 'class': 'logging.handlers.WatchedFileHandler',
                 'formatter': 'simple',
                 'filename': '/var/log/fred-webwhois.log'},
    },
    'loggers': {
        '': {'handlers': ['file'],
             'level': 'DEBUG'},
    },
}
