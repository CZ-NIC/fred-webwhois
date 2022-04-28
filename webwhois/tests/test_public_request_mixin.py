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
from datetime import datetime
from typing import Any, List
from unittest.mock import _Call, call, patch

from django.test import SimpleTestCase, override_settings
from django.test.client import RequestFactory
from fred_idl.Registry.PublicRequest import OBJECT_NOT_FOUND
from grill.utils import TestLogEntry as _TestLogEntry, TestLoggerClient as _TestLoggerClient

from webwhois.constants import PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType, PublicRequestsLogResult
from webwhois.forms import SendPasswordForm
from webwhois.forms.public_request import ConfirmationMethod
from webwhois.forms.widgets import DeliveryType
from webwhois.tests.utils import apply_patch
from webwhois.views.public_request_mixin import PublicRequestFormView, PublicRequestKnownException, cache


class TestLoggerClient(_TestLoggerClient):
    def create_log_entry(self, *args: Any, **kwargs: Any) -> str:
        super().create_log_entry(*args, **kwargs)
        # XXX: Return logger-like identifier to pass the old ID backport hook.
        return '42.log-entry-id'


class TestLogEntry(_TestLogEntry):
    def get_calls(self) -> List[_Call]:
        calls = super().get_calls()
        # XXX: Replace logger-like identifier in the close call.
        close_call = calls[1]
        calls[1] = getattr(call, close_call[0])('42.log-entry-id', *close_call[1][1:], **close_call[2])
        return calls


class TestException(Exception):
    "Test exception"


class DebugPublicRequest(PublicRequestFormView):

    public_key = "debug_public_key"
    log_entry_type = 'fooActionName'

    def __init__(self):
        self.request = RequestFactory().get('/dummy/')

    def _call_registry_command(self, data, log_request_id):
        return 42

    def get_public_response(self, form, public_request_id):
        return {'cleaned_data': form.cleaned_data, 'public_request_id': public_request_id}


class DebugPublicRequestKnownException(DebugPublicRequest):

    def _call_registry_command(self, data, log_request_id):
        raise PublicRequestKnownException(type(OBJECT_NOT_FOUND()).__name__)


class DebugPublicRequestRaiseException(DebugPublicRequest):

    def _call_registry_command(self, data, log_request_id):
        raise TestException()


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class TestPublicRequestFormView(SimpleTestCase):

    def setUp(self):
        self.test_logger = TestLoggerClient()
        log_patcher = patch('webwhois.utils.corba_wrapper.PUBLIC_REQUESTS_LOGGER.client', new=self.test_logger)
        self.addCleanup(log_patcher.stop)
        log_patcher.start()

        apply_patch(self, patch("webwhois.views.public_request_mixin.get_random_string", lambda n: "foooo"))

    def tearDown(self):
        cache.clear()

    def _get_send_password_form(self, pubreq):
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        })
        self.assertTrue(form.is_valid())
        return form

    @patch("webwhois.utils.public_response.localdate")
    def test_logged_call_to_registry(self, mock_localdate):
        mock_localdate.return_value = datetime(2017, 3, 8)
        pubreq = DebugPublicRequest()
        form = self._get_send_password_form(pubreq)
        pubreq.logged_call_to_registry(form)
        cleaned_data = {
            'handle': 'foo.cz',
            'object_type': 'domain',
            'confirmation_method': ConfirmationMethod.SIGNED_EMAIL,
            'send_to': DeliveryType('email_in_registry', ''),
        }
        self.assertEqual(cache.get(pubreq.public_key), {'cleaned_data': cleaned_data, 'public_request_id': 42})

        # Check logger
        properties = {'handle': 'foo.cz', 'handleType': 'domain', 'confirmMethod': 'signed_email',
                      'sendTo': 'email_in_registry'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.AUTH_INFO,
                                 PublicRequestsLogResult.SUCCESS, source_ip='127.0.0.1', input_properties=properties,
                                 references={'publicrequest': '42'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_logged_call_with_known_exception(self):
        pubreq = DebugPublicRequestKnownException()
        form = self._get_send_password_form(pubreq)
        with self.assertRaises(PublicRequestKnownException):
            pubreq.logged_call_to_registry(form)
        self.assertIsNone(cache.get(pubreq.public_key))

        # Check logger
        properties = {'handle': 'foo.cz', 'handleType': 'domain', 'confirmMethod': 'signed_email',
                      'sendTo': 'email_in_registry'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.AUTH_INFO,
                                 PublicRequestsLogResult.FAIL, source_ip='127.0.0.1', input_properties=properties,
                                 properties={'reason': 'OBJECT_NOT_FOUND'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_logged_call_raise_exception(self):
        pubreq = DebugPublicRequestRaiseException()
        form = self._get_send_password_form(pubreq)
        with self.assertRaises(TestException):
            pubreq.logged_call_to_registry(form)
        self.assertIsNone(cache.get(pubreq.public_key))

        # Check logger
        properties = {'handle': 'foo.cz', 'handleType': 'domain', 'confirmMethod': 'signed_email',
                      'sendTo': 'email_in_registry'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.AUTH_INFO,
                                 PublicRequestsLogResult.ERROR, source_ip='127.0.0.1', input_properties=properties,
                                 properties={'exception': 'TestException'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())
