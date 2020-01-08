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
from django.core.cache import cache
from django.utils.crypto import get_random_string
from django.views.generic import FormView
from fred_idl.Registry.PublicRequest import ObjectType_PR

from webwhois.utils.corba_wrapper import LOGGER
from webwhois.views.logger_mixin import LoggerMixin


class PublicRequestKnownException(Exception):
    """Used for displaying message on the form."""

    def __init__(self, exception_code_name):
        self.exception_code_name = exception_code_name


class PublicRequestLoggerMixin(LoggerMixin):
    """Mixin for logging request if LOGGER is set."""

    service_name = "Public Request"

    def finish_logging_request(self, log_request, response_id, error_object):
        """
        Finish logging request.

        @param log_request: Logger instace.
        @param response_id: Response ID. It can be None. None causes the request result is 'Fail'.
        @param error_object: Error object of python exception or corba exception.
        """
        if log_request is None:
            return
        properties_out, references = [], []
        if error_object:
            if isinstance(error_object, PublicRequestKnownException):
                properties_out.append(("reason", error_object.exception_code_name))
                log_request.result = "Fail"
            else:
                # Default result is "Error"
                properties_out.append(("exception", error_object.__class__.__name__))
        else:
            if response_id:
                references.append(('publicrequest', response_id))
                log_request.result = "Ok"
            else:
                log_request.result = "Fail"
        log_request.close(properties=properties_out, references=references)


class PublicRequestFormView(PublicRequestLoggerMixin, FormView):
    """FormView for manage public requests. Logs calls to the registry if LOGGER is set."""

    public_key = None  # public key for the cache key with a response values.

    def _get_object_type(self, name):
        return {
            'domain': ObjectType_PR.domain,
            'contact': ObjectType_PR.contact,
            'nsset': ObjectType_PR.nsset,
            'keyset': ObjectType_PR.keyset
        }[name]

    def _call_registry_command(self, form, log_request_id):
        """Call a registry command. Return public_request_id or raise exception if the call failed."""
        raise NotImplementedError

    def get_public_response(self, form, public_request_id):
        """Return a public response object."""
        raise NotImplementedError

    def logged_call_to_registry(self, form):
        """
         Log the call to the registry.

        @param form: Django form instance with cleaned_data.
        @return: Response ID.
        """
        self.public_key = get_random_string(64)
        if LOGGER:
            log_request = self.prepare_logging_request(form.cleaned_data)
            log_request_id = log_request.request_id
        else:
            log_request = log_request_id = None
        public_request_id = error = None
        try:
            public_request_id = self._call_registry_command(form, log_request_id)
            public_response = self.get_public_response(form, public_request_id)
            cache.set(self.public_key, public_response, 60 * 60 * 24)
        except BaseException as err:
            error = err
            raise
        finally:
            self.finish_logging_request(log_request, public_request_id, error)

    def form_valid(self, form):
        try:
            self.logged_call_to_registry(form)
        except PublicRequestKnownException:
            return self.form_invalid(form)
        self.form_cleaned_data = form.cleaned_data
        return super(PublicRequestFormView, self).form_valid(form)
