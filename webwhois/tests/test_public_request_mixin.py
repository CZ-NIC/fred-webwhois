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
from unittest.mock import call, patch

from django.test import SimpleTestCase, override_settings
from django.test.client import RequestFactory
from fred_idl.Registry.PublicRequest import OBJECT_NOT_FOUND

from webwhois.constants import PublicRequestsLogEntryType
from webwhois.forms import SendPasswordForm
from webwhois.forms.public_request import ConfirmationMethod
from webwhois.forms.widgets import DeliveryType
from webwhois.tests.utils import apply_patch
from webwhois.views.public_request_mixin import PublicRequestFormView, PublicRequestKnownException, cache


class TestException(Exception):
    "Test exception"


class DebugPublicRequest(PublicRequestFormView):

    public_key = "debug_public_key"

    def __init__(self):
        self.request = RequestFactory().request()

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
        self.LOGGER = apply_patch(self, patch("webwhois.views.public_request_mixin.LOGGER"))
        apply_patch(self, patch("webwhois.views.logger_mixin.LOGGER", self.LOGGER))
        apply_patch(self, patch("webwhois.views.public_request_mixin.get_random_string", lambda n: "foooo"))

    def tearDown(self):
        cache.clear()

    def test_finish_logging_request(self):
        self.LOGGER.result = 'Error'
        pubreq = DebugPublicRequest()
        pubreq.finish_logging_request(self.LOGGER, 42, None)
        self.assertEqual(self.LOGGER.mock_calls, [call.close(properties=[], references=[('publicrequest', 42)])])
        self.assertEqual(self.LOGGER.result, 'Ok')

    def test_finish_logging_request_unexpected_exception(self):
        self.LOGGER.result = 'Error'
        pubreq = DebugPublicRequest()
        pubreq.finish_logging_request(self.LOGGER, None, TestException())
        self.assertEqual(self.LOGGER.mock_calls, [call.close(properties=[('exception', 'TestException')],
                                                             references=[])])
        self.assertEqual(self.LOGGER.result, 'Error')

    def test_finish_logging_request_with_known_exception(self):
        self.LOGGER.result = 'Error'
        pubreq = DebugPublicRequest()
        pubreq.finish_logging_request(self.LOGGER, None, PublicRequestKnownException(
            type(OBJECT_NOT_FOUND()).__name__))
        self.assertEqual(self.LOGGER.mock_calls, [call.close(properties=[('reason', 'OBJECT_NOT_FOUND')],
                                                             references=[])])
        self.assertEqual(self.LOGGER.result, 'Fail')

    def test_finish_logging_request_no_response_id(self):
        self.LOGGER.result = 'Error'
        pubreq = DebugPublicRequest()
        pubreq.finish_logging_request(self.LOGGER, None, None)
        self.assertEqual(self.LOGGER.mock_calls, [call.close(properties=[], references=[])])
        self.assertEqual(self.LOGGER.result, 'Fail')

    @patch("webwhois.views.public_request_mixin.LOGGER", None)
    @patch("webwhois.utils.public_response.localdate")
    def test_logged_call_to_registry_no_logger(self, mock_localdate):
        mock_localdate.return_value = datetime(2017, 3, 8)
        pubreq = DebugPublicRequest()
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        })
        self.assertTrue(form.is_valid())
        pubreq.logged_call_to_registry(form)
        cleaned_data = {
            'handle': 'foo.cz',
            'object_type': 'domain',
            'confirmation_method': ConfirmationMethod.SIGNED_EMAIL,
            'send_to': DeliveryType('email_in_registry', ''),
        }
        self.assertEqual(cache.get(pubreq.public_key), {'cleaned_data': cleaned_data, 'public_request_id': 42})
        self.assertEqual(self.LOGGER.mock_calls, [])

    def _init_logger(self):
        self.LOGGER.create_request.return_value.request_id = 42
        self.LOGGER.create_request.return_value.result = 'Error'

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
        self._init_logger()
        pubreq = DebugPublicRequest()
        form = self._get_send_password_form(pubreq)
        pubreq.logged_call_to_registry(form)
        properties = [('handle', 'foo.cz'), ('handleType', 'domain'), ('confirmMethod', 'signed_email'),
                      ('sendTo', 'email_in_registry')]
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', PublicRequestsLogEntryType.AUTH_INFO, properties=properties),
            call().close(properties=[], references=[('publicrequest', 42)]),
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')
        cleaned_data = {
            'handle': 'foo.cz',
            'object_type': 'domain',
            'confirmation_method': ConfirmationMethod.SIGNED_EMAIL,
            'send_to': DeliveryType('email_in_registry', ''),
        }
        self.assertEqual(cache.get(pubreq.public_key), {'cleaned_data': cleaned_data, 'public_request_id': 42})

    def test_logged_call_with_known_exception(self):
        self._init_logger()
        pubreq = DebugPublicRequestKnownException()
        form = self._get_send_password_form(pubreq)
        with self.assertRaises(PublicRequestKnownException):
            pubreq.logged_call_to_registry(form)
        properties = [('handle', 'foo.cz'), ('handleType', 'domain'), ('confirmMethod', 'signed_email'),
                      ('sendTo', 'email_in_registry')]
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', PublicRequestsLogEntryType.AUTH_INFO, properties=properties),
            call().close(properties=[('reason', 'OBJECT_NOT_FOUND')], references=[]),
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Fail')
        self.assertIsNone(cache.get(pubreq.public_key))

    def test_logged_call_raise_exception(self):
        self._init_logger()
        pubreq = DebugPublicRequestRaiseException()
        form = self._get_send_password_form(pubreq)
        with self.assertRaises(TestException):
            pubreq.logged_call_to_registry(form)
        properties = [('handle', 'foo.cz'), ('handleType', 'domain'), ('confirmMethod', 'signed_email'),
                      ('sendTo', 'email_in_registry')]
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', PublicRequestsLogEntryType.AUTH_INFO, properties=properties),
            call().close(properties=[('exception', 'TestException')], references=[]),
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Error')
        self.assertIsNone(cache.get(pubreq.public_key))
