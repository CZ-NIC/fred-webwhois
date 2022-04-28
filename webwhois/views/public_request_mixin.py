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
from typing import cast

from django.core.cache import cache
from django.utils.crypto import get_random_string
from django.views.generic import FormView
from fred_idl.Registry.PublicRequest import ObjectType_PR

from webwhois.utils.corba_wrapper import PUBLIC_REQUESTS_LOGGER, _backport_log_entry_id

from ..constants import PublicRequestsLogResult


class PublicRequestKnownException(Exception):
    """Used for displaying message on the form."""

    def __init__(self, exception_code_name):
        self.exception_code_name = exception_code_name


class PublicRequestFormView(FormView):
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
        """Log the call to the registry.

        @param form: Django form instance with cleaned_data.
        @return: Response ID.
        """
        self.public_key = get_random_string(64)
        with PUBLIC_REQUESTS_LOGGER.create(form.log_entry_type, source_ip=self.request.META.get('REMOTE_ADDR', ''),
                                           properties=form.get_log_properties()) as log_entry:
            try:
                public_request_id = self._call_registry_command(form,
                                                                _backport_log_entry_id(cast(str, log_entry.entry_id)))
                public_response = self.get_public_response(form, public_request_id)
                cache.set(self.public_key, public_response, 60 * 60 * 24)
            except PublicRequestKnownException as error:
                log_entry.properties["reason"] = error.exception_code_name
                log_entry.result = PublicRequestsLogResult.FAIL
                raise
            except BaseException as error:
                log_entry.properties["exception"] = type(error).__name__
                raise
            else:
                if public_request_id:
                    log_entry.references['publicrequest'] = str(public_request_id)
                    log_entry.result = PublicRequestsLogResult.SUCCESS
                else:
                    log_entry.result = PublicRequestsLogResult.FAIL

    def form_valid(self, form):
        try:
            self.logged_call_to_registry(form)
        except PublicRequestKnownException:
            return self.form_invalid(form)
        self.form_cleaned_data = form.cleaned_data
        return super(PublicRequestFormView, self).form_valid(form)
