# -*- coding: utf-8 -*-
#
# Copyright (C) 2018-2019  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

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
    'webwhois.apps.WebwhoisAppConfig',
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
