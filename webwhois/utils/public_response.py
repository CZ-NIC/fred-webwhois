"""
Public responses - responses for public requests.

Responses hold the data to be displayed on the response pages.
"""
from __future__ import unicode_literals

from datetime import date

from django.conf import settings
from django.utils.timezone import localdate


class PublicResponse(object):
    """Base class for public responses."""

    def __init__(self, object_type, public_request_id, request_type, handle):
        self.object_type = object_type
        self.public_request_id = public_request_id
        self.handle = handle
        self.request_type = request_type
        if settings.USE_TZ:
            self.create_date = localdate()
        else:
            self.create_date = date.today()

    def __repr__(self):
        output = '<{cls} {object_type} {handle} {public_request_id}>'.format(
            cls=unicode(type(self).__name__), object_type=self.object_type, handle=self.handle,
            public_request_id=self.public_request_id)
        return output.encode('utf-8')

    def __eq__(self, other):
        return type(self) == type(other) and self.object_type == other.object_type \
            and self.public_request_id == other.public_request_id and self.request_type == other.request_type \
            and self.handle == other.handle and self.create_date == other.create_date

    def __ne__(self, other):
        return not self == other


class SendPasswordResponse(PublicResponse):
    """Public response for send password public request."""

    def __init__(self, object_type, public_request_id, request_type, handle, custom_email):
        super(SendPasswordResponse, self).__init__(object_type, public_request_id, request_type, handle)
        self.custom_email = custom_email

    def __eq__(self, other):
        return super(SendPasswordResponse, self).__eq__(other) and self.custom_email == other.custom_email


class PersonalInfoResponse(PublicResponse):
    """Public response for personal info public request."""

    def __init__(self, object_type, public_request_id, request_type, handle, custom_email):
        super(PersonalInfoResponse, self).__init__(object_type, public_request_id, request_type, handle)
        self.custom_email = custom_email

    def __eq__(self, other):
        return super(PersonalInfoResponse, self).__eq__(other) and self.custom_email == other.custom_email


class BlockResponse(PublicResponse):
    """Public response for block public requests."""

    def __init__(self, object_type, public_request_id, request_type, handle, action, lock_type):
        super(BlockResponse, self).__init__(object_type, public_request_id, request_type, handle)
        self.action = action
        self.lock_type = lock_type

    def __eq__(self, other):
        return super(BlockResponse, self).__eq__(other) and self.action == other.action \
            and self.lock_type == other.lock_type
