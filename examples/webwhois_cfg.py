#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Example django settings for webwhois project.

Do not use on production - DEBUG settings are turned on.
"""
###############################################################################
#                  Webwhois Server Configuration File                         #
###############################################################################

# ## Django Settings ##########################################################
#
# Note: Refer to the Django documentation for a description.
SECRET_KEY = 'SecretKey'
DEBUG = True
ALLOWED_HOSTS = ['*']


INSTALLED_APPS = (
    'django.contrib.staticfiles',
    'webwhois',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/webwhois_cache',
    },
}

MIDDLEWARE = (
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'webwhois_urls'

STATIC_URL = '/static/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
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
        'console': {'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple'},
    },
    'loggers': {
        '': {'handlers': ['console'],
             'level': 'DEBUG'},
    },
}
