#
# Copyright (C) 2017-2020  CZ.NIC, z. s. p. o.
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

"""LoggerMixin for views."""
from webwhois.utils.corba_wrapper import LOGGER


class LoggerMixin(object):
    """Create LogRequest. Force implementation of finish_logging_request, _get_logging_request_name_and_properties."""

    service_name = None

    def prepare_logging_request(self, cleaned_data):
        """Prepare logging request.

        @param cleaned_data: Cleaned data for logger properties.
        @type cleaned_data: C{dict}
        @return: LogRequest instance.
        """
        request_name, properties_in = self._get_logging_request_name_and_properties(cleaned_data)
        return LOGGER.create_request(self.request.META.get('REMOTE_ADDR', ''), self.service_name, request_name,
                                     properties=properties_in)

    def _get_logging_request_name_and_properties(self, data):
        """Return request_name and properties_in for logger. Derived class must implement this method."""
        raise NotImplementedError

    def finish_logging_request(self, *args, **kwargs):
        """Finish logging request. Derived class must implement this method."""
        raise NotImplementedError
