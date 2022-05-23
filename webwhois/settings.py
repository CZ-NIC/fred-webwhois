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
import os
from functools import partial
from typing import Any, Dict

from appsettings import AppSettings, DictSetting, FileSetting, Setting, StringSetting
from django.core.exceptions import ValidationError
from frgal import make_credentials


def timeout_validator(value: Any) -> None:
    """Validate timeouts - must contain a number or tuple with two numbers."""
    if isinstance(value, (float, int)):
        return
    if isinstance(value, tuple) and len(value) == 2 and all(isinstance(v, (float, int)) for v in value):
        return
    raise ValidationError('Value %(value)s must be a float, int or a tuple with 2 float or int items.',
                          params={'value': value})


class LoggerOptionsSetting(DictSetting):
    """Custom dict setting for logger options."""

    def transform(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Transform the credentials."""
        value = super().transform(value)
        if 'credentials' in value:
            value['credentials'] = make_credentials(**value['credentials'])
        return value


class WebwhoisAppSettings(AppSettings):
    """Web whois settings."""

    CDNSKEY_NETLOC = StringSetting(default=None)
    CDNSKEY_SSL_CERT = FileSetting(default=None, mode=os.R_OK)
    CORBA_NETLOC = StringSetting(default=partial(os.environ.get, 'FRED_WEBWHOIS_NETLOC', 'localhost'))
    CORBA_CONTEXT = StringSetting(default='fred')
    LOGGER = StringSetting(default='grill.DummyLoggerClient')
    LOGGER_OPTIONS = LoggerOptionsSetting(default={})
    REGISTRY_NETLOC = StringSetting(required=True)
    REGISTRY_SSL_CERT = FileSetting(default=None, mode=os.R_OK)
    SECRETARY_URL = StringSetting(required=True)
    SECRETARY_AUTH = Setting()
    SECRETARY_TIMEOUT = Setting(default=3.05, validators=[timeout_validator])

    class Meta:
        setting_prefix = 'WEBWHOIS_'


WEBWHOIS_SETTINGS = WebwhoisAppSettings()
