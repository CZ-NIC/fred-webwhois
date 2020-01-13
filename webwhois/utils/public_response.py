#
# Copyright (C) 2018-2020  CZ.NIC, z. s. p. o.
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

"""Public responses - responses for public requests.

Responses hold the data to be displayed on the response pages.
"""
import warnings
from datetime import date

from django.conf import settings
from django.utils.timezone import localdate

UNDEFINED = 'UNDEFINED'


class PublicResponse(object):
    """Base class for public responses."""

    def __init__(self, object_type, public_request_id, request_type, handle, confirmation_method=UNDEFINED):
        self.object_type = object_type
        self.public_request_id = public_request_id
        self.handle = handle
        self.request_type = request_type
        if confirmation_method == UNDEFINED:
            warnings.warn("Argument confirmation_method will be required.", DeprecationWarning)
            confirmation_method = None
        self.confirmation_method = confirmation_method
        if settings.USE_TZ:
            self.create_date = localdate()
        else:
            self.create_date = date.today()

    def __repr__(self):
        return '<{cls} {object_type} {handle} {public_request_id}>'.format(
            cls=str(type(self).__name__), object_type=self.object_type, handle=self.handle,
            public_request_id=self.public_request_id)

    def __eq__(self, other):
        return type(self) == type(other) and self.object_type == other.object_type \
            and self.public_request_id == other.public_request_id and self.request_type == other.request_type \
            and self.handle == other.handle and self.create_date == other.create_date \
            and self.confirmation_method == other.confirmation_method

    def __ne__(self, other):
        return not self == other


class SendPasswordResponse(PublicResponse):
    """Public response for send password public request."""

    def __init__(self, object_type, public_request_id, request_type, handle, custom_email,
                 confirmation_method=UNDEFINED):
        super(SendPasswordResponse, self).__init__(object_type, public_request_id, request_type, handle,
                                                   confirmation_method)
        self.custom_email = custom_email

    def __eq__(self, other):
        return super(SendPasswordResponse, self).__eq__(other) and self.custom_email == other.custom_email


class PersonalInfoResponse(PublicResponse):
    """Public response for personal info public request."""

    def __init__(self, object_type, public_request_id, request_type, handle, custom_email,
                 confirmation_method=UNDEFINED):
        super(PersonalInfoResponse, self).__init__(object_type, public_request_id, request_type, handle,
                                                   confirmation_method)
        self.custom_email = custom_email

    def __eq__(self, other):
        return super(PersonalInfoResponse, self).__eq__(other) and self.custom_email == other.custom_email


class BlockResponse(PublicResponse):
    """Public response for block public requests."""

    def __init__(self, object_type, public_request_id, request_type, handle, action, lock_type,
                 confirmation_method=UNDEFINED):
        super(BlockResponse, self).__init__(object_type, public_request_id, request_type, handle, confirmation_method)
        self.action = action
        self.lock_type = lock_type

    def __eq__(self, other):
        return super(BlockResponse, self).__eq__(other) and self.action == other.action \
            and self.lock_type == other.lock_type
