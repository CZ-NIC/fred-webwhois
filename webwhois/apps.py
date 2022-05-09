#
# Copyright (C) 2017-2022  CZ.NIC, z. s. p. o.
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
"""AppConfig definition."""
from django.apps import AppConfig

from .settings import WebwhoisAppSettings


class WebwhoisAppConfig(AppConfig):
    name = 'webwhois'

    def ready(self) -> None:
        from webwhois.utils.corba_wrapper import LOGGER

        from .constants import (LOGGER_SERVICE, PUBLIC_REQUESTS_LOGGER_SERVICE, LogEntryType, LogResult,
                                PublicRequestsLogEntryType, PublicRequestsLogResult)

        WebwhoisAppSettings.check()

        LOGGER.client.register_service(LOGGER_SERVICE, handle='webwhois_')
        LOGGER.client.register_log_entry_types(LOGGER_SERVICE, LogEntryType)
        LOGGER.client.register_results(LOGGER_SERVICE, LogResult)

        LOGGER.client.register_service(PUBLIC_REQUESTS_LOGGER_SERVICE, handle='pubreq_')
        LOGGER.client.register_log_entry_types(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType)
        LOGGER.client.register_results(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogResult)
