#
# Copyright (C) 2016-2020  CZ.NIC, z. s. p. o.
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
import os
from functools import partial

from appsettings import AppSettings, Setting, StringSetting
from django.conf import settings


def _get_logger_defalt(setting_name):
    return getattr(WEBWHOIS_SETTINGS, setting_name)


class WebwhoisAppSettings(AppSettings):
    """Web whois settings."""

    CORBA_NETLOC = StringSetting(default=partial(os.environ.get, 'FRED_WEBWHOIS_NETLOC', 'localhost'))
    CORBA_CONTEXT = StringSetting(default='fred')
    LOGGER = Setting(default='pylogger.corbalogger.Logger')
    LOGGER_CORBA_NETLOC = StringSetting(default=partial(_get_logger_defalt, 'CORBA_NETLOC'))
    LOGGER_CORBA_CONTEXT = StringSetting(default=partial(_get_logger_defalt, 'CORBA_CONTEXT'))

    class Meta:
        setting_prefix = 'WEBWHOIS_'


WEBWHOIS_SETTINGS = WebwhoisAppSettings()

WEBWHOIS_DNSSEC_URL = getattr(settings, 'WEBWHOIS_DNSSEC_URL', None)

# Groups names that will be displayed with/without certifications.
WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED = getattr(settings, 'WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED', None)
WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED = getattr(settings, 'WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED', None)
