#
# Copyright (C) 2016-2022  CZ.NIC, z. s. p. o.
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
#
INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'webwhois.tests.apps.TestWebwhoisAppConfig',
)
ROOT_URLCONF = 'webwhois.urls'
SECRET_KEY = 'SECRET'
STATIC_URL = '/static/'

WEBWHOIS_CORBA_EXPORT_MODULES = ('Registry', 'ccReg')
WEBWHOIS_CAPTCHA_MAX_REQUESTS = 100
WEBWHOIS_REGISTRY_NETLOC = "example.org:50000"
WEBWHOIS_SECRETARY_URL = 'http://example.org:8000/'
