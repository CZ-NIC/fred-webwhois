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
import warnings
from datetime import date
from typing import Any, Dict, List
from unittest.mock import _Call, call, patch, sentinel

from django.core.cache import cache
from django.http import HttpResponseNotFound
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils.html import escape
from fred_idl.Registry.PublicRequest import (HAS_DIFFERENT_BLOCK, INVALID_EMAIL, OBJECT_ALREADY_BLOCKED,
                                             OBJECT_NOT_BLOCKED, OBJECT_NOT_FOUND, OBJECT_TRANSFER_PROHIBITED,
                                             OPERATION_PROHIBITED, ConfirmedBy, Language, LockRequestType,
                                             ObjectType_PR)
from grill.utils import TestLogEntry as _TestLogEntry, TestLoggerClient as _TestLoggerClient

from webwhois.constants import PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType, PublicRequestsLogResult
from webwhois.forms.public_request import ConfirmationMethod
from webwhois.forms.widgets import DeliveryType
from webwhois.tests.utils import TEMPLATES, apply_patch
from webwhois.utils import PUBLIC_REQUEST
from webwhois.utils.public_response import BlockResponse, PersonalInfoResponse, PublicResponse, SendPasswordResponse


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


@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestForms(SimpleTestCase):

    def test_send_password(self):
        response = self.client.get(reverse("webwhois:form_send_password"))
        self.assertContains(response, "Request to send a password (authinfo)")

    def test_block_object(self):
        response = self.client.get(reverse("webwhois:form_block_object"))
        self.assertContains(response, "Block")

    def test_unblock_object(self):
        response = self.client.get(reverse("webwhois:form_unblock_object"))
        self.assertContains(response, "Unblock")

    def test_form_param_send_to(self):
        params = "?handle=foo&object_type=nsset&send_to=custom_email"
        response = self.client.get(reverse("webwhois:form_send_password") + params)
        self.assertContains(response, "password (authinfo)")
        self.assertEqual(response.context['form'].initial, {'object_type': 'nsset', 'handle': 'foo',
                                                            'send_to': DeliveryType('custom_email', '')})

    def test_form_param_block_unblock(self):
        params = "?handle=foo&object_type=nsset&lock_type=all"
        response = self.client.get(reverse("webwhois:form_block_object") + params)
        self.assertContains(response, "Block")
        self.assertEqual(response.context['form'].initial, {'handle': 'foo', 'lock_type': 'all',
                                                            'object_type': 'nsset'})


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
                   SESSION_ENGINE='django.contrib.sessions.backends.cache', ROOT_URLCONF='webwhois.tests.urls',
                   MIDDLEWARE=('django.contrib.sessions.middleware.SessionMiddleware',))
class SubmittedFormTestCase(SimpleTestCase):

    public_key = "1234567890123456789012345678901234567890123456789012345678901234"

    def setUp(self):
        spec = ('create_authinfo_request_non_registry_email', 'create_authinfo_request_registry_email',
                'create_block_unblock_request', 'create_personal_info_request_registry_email',
                'create_personal_info_request_non_registry_email')
        apply_patch(self, patch.object(PUBLIC_REQUEST, 'client', spec=spec))

        self.test_logger = TestLoggerClient()
        log_patcher = patch('webwhois.utils.corba_wrapper.PUBLIC_REQUESTS_LOGGER.client', new=self.test_logger)
        self.addCleanup(log_patcher.stop)
        log_patcher.start()

        localdate_patcher = patch("webwhois.utils.public_response.localdate", return_value=date(2017, 3, 8))
        apply_patch(self, localdate_patcher)
        apply_patch(self, patch("webwhois.views.public_request_mixin.get_random_string", lambda n: self.public_key))

    def tearDown(self):
        cache.clear()


@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestBaseResponseTemplateView(SimpleTestCase):
    """Test BaseResponseTemplateView class."""

    def test_context(self):
        public_response = PublicResponse('android', 42, 'WashListersUnderpants', 'KRYTEN', None)
        cache.set('test-public-key', public_response)

        response = self.client.get('/base-public-response/')

        self.assertEqual(response.context['public_response'], public_response)


@override_settings(TEMPLATES=TEMPLATES, USE_TZ=True)
class TestSendPasswodForm(SubmittedFormTestCase):
    def setUp(self):
        super().setUp()

        catcher = warnings.catch_warnings(record=True)
        self.addCleanup(catcher.__exit__)
        catcher.__enter__()

    def _send_password_email_in_registry(self, post: Dict, action_name: str, properties: Dict[str, Any],
                                         object_type: str, title: str) -> None:
        PUBLIC_REQUEST.create_authinfo_request_registry_email.return_value = 24
        response = self.client.post(reverse("webwhois:form_send_password"), post, follow=True)
        path = reverse("webwhois:email_in_registry_response", kwargs={"public_key": self.public_key})
        self.assertRedirects(response, path)
        self.assertContains(response, title)
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_authinfo_request_registry_email(object_type, post['handle'], 42)
        ])

        # Check logger
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.AUTH_INFO,
                                 PublicRequestsLogResult.SUCCESS, source_ip='127.0.0.1',
                                 input_properties=properties,
                                 references={'publicrequest': '24'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_send_password_email_in_registry_domain(self):
        post = {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        }
        properties = {'handle': 'foo.cz', 'handleType': 'domain', 'sendTo': 'email_in_registry',
                      'confirmMethod': 'signed_email'}
        object_type = ObjectType_PR.domain
        title = "Request to send a password (authinfo) for transfer domain name foo.cz"
        self._send_password_email_in_registry(post, 'AuthInfo', properties, object_type, title)

    def test_send_password_email_in_registry_contact(self):
        post = {
            "object_type": "contact",
            "handle": "CONTACT",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        }
        properties = {'handle': 'CONTACT', 'handleType': 'contact', 'sendTo': 'email_in_registry',
                      'confirmMethod': 'signed_email'}
        object_type = ObjectType_PR.contact
        title = "Request to send a password (authinfo) for transfer contact CONTACT"
        self._send_password_email_in_registry(post, 'AuthInfo', properties, object_type, title)

    def test_send_password_email_in_registry_nsset(self):
        post = {
            "object_type": "nsset",
            "handle": "NSSET",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        }
        properties = {'handle': 'NSSET', 'handleType': 'nsset', 'sendTo': 'email_in_registry',
                      'confirmMethod': 'signed_email'}
        object_type = ObjectType_PR.nsset
        title = "Request to send a password (authinfo) for transfer nameserver set NSSET"
        self._send_password_email_in_registry(post, 'AuthInfo', properties, object_type, title)

    def test_send_password_email_in_registry_keyset(self):
        post = {
            "object_type": "keyset",
            "handle": "KEYSET",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        }
        properties = {'handle': 'KEYSET', 'handleType': 'keyset', 'sendTo': 'email_in_registry',
                      'confirmMethod': 'signed_email'}
        object_type = ObjectType_PR.keyset
        title = "Request to send a password (authinfo) for transfer keyset KEYSET"
        self._send_password_email_in_registry(post, 'AuthInfo', properties, object_type, title)

    def _assert_send_password_exception(self, exception_code, form_error_message):
        post = {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        }
        response = self.client.post(reverse("webwhois:form_send_password"), post)
        self.assertEqual(response.context['form'].errors, {'handle': [form_error_message]})
        self.assertContains(response, form_error_message)
        object_type = ObjectType_PR.domain
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_authinfo_request_registry_email(object_type, 'foo.cz', 42)
        ])

        # Check logger
        properties = {'handle': 'foo.cz', 'handleType': 'domain', 'sendTo': 'email_in_registry',
                      'confirmMethod': 'signed_email'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.AUTH_INFO,
                                 PublicRequestsLogResult.FAIL, source_ip='127.0.0.1',
                                 input_properties=properties, properties={'reason': exception_code})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_send_password_object_not_found(self):
        PUBLIC_REQUEST.create_authinfo_request_registry_email.side_effect = OBJECT_NOT_FOUND
        self._assert_send_password_exception('OBJECT_NOT_FOUND', 'Object not found. Check that you have correctly '
                                             'entered the Object type and Handle.')

    def test_send_password_object_transfer_prohibited(self):
        PUBLIC_REQUEST.create_authinfo_request_registry_email.side_effect = \
            OBJECT_TRANSFER_PROHIBITED
        self._assert_send_password_exception('OBJECT_TRANSFER_PROHIBITED', 'Transfer of object is prohibited. '
                                             'The request can not be accepted.')

    def test_send_password_invalid_email(self):
        PUBLIC_REQUEST.create_authinfo_request_non_registry_email.side_effect = INVALID_EMAIL
        post = {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to_0": "custom_email",
            "send_to_1": "foo@foo.off",
        }
        response = self.client.post(reverse("webwhois:form_send_password"), post)
        self.assertEqual(response.context['form'].errors, {
            'send_to': ['The email was not found or the address is not valid.']
        })
        self.assertContains(response, 'The email was not found or the address is not valid.')
        object_type = ObjectType_PR.domain
        signed_email = ConfirmedBy.signed_email
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_authinfo_request_non_registry_email(object_type, 'foo.cz', 42, signed_email, 'foo@foo.off')
        ])

        # Check logger
        properties = {'handle': 'foo.cz', 'handleType': 'domain', 'sendTo': 'custom_email',
                      'confirmMethod': 'signed_email', 'customEmail': 'foo@foo.off'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.AUTH_INFO,
                                 PublicRequestsLogResult.FAIL, source_ip='127.0.0.1',
                                 input_properties=properties, properties={'reason': 'INVALID_EMAIL'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def _send_password_confirm_method(self, confirm_method, post, action_name, properties, object_type, title):
        PUBLIC_REQUEST.create_authinfo_request_non_registry_email.return_value = 24
        response = self.client.post(reverse("webwhois:form_send_password"), post, follow=True)
        self.assertRedirects(response, reverse("webwhois:public_response", kwargs={"public_key": self.public_key}))
        self.assertContains(response, title)
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_authinfo_request_non_registry_email(object_type, post['handle'], 42, confirm_method,
                                                            'foo@foo.off')
        ])

        # Check logger
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.AUTH_INFO,
                                 PublicRequestsLogResult.SUCCESS, source_ip='127.0.0.1',
                                 input_properties=properties, references={'publicrequest': '24'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def _send_password_to_custom_email(self, post: Dict, action_name: str, properties: Dict[str, Any], object_type: str,
                                       title: str) -> None:
        conftype = ConfirmedBy.signed_email
        self._send_password_confirm_method(conftype, post, action_name, properties, object_type, title)

    def _send_password_notarized_letter(self, post: Dict, action_name: str, properties: Dict[str, Any],
                                        object_type: str, title: str) -> None:
        conftype = ConfirmedBy.notarized_letter
        self._send_password_confirm_method(conftype, post, action_name, properties, object_type, title)

    def test_send_password_custom_email_domain(self):
        post = {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to_0": "custom_email",
            "send_to_1": "foo@foo.off",
        }
        properties = {'handle': 'foo.cz', 'handleType': 'domain', 'sendTo': 'custom_email',
                      'confirmMethod': 'signed_email', 'customEmail': 'foo@foo.off'}
        object_type = ObjectType_PR.domain
        title = "Request summary"
        self._send_password_to_custom_email(post, 'AuthInfo', properties, object_type, title)

    def test_send_password_custom_email_contact(self):
        post = {
            "object_type": "contact",
            "handle": "FOO",
            "confirmation_method": "signed_email",
            "send_to_0": "custom_email",
            "send_to_1": "foo@foo.off",
        }
        properties = {'handle': 'FOO', 'handleType': 'contact', 'sendTo': 'custom_email',
                      'confirmMethod': 'signed_email', 'customEmail': 'foo@foo.off'}
        object_type = ObjectType_PR.contact
        title = "Request summary"
        self._send_password_to_custom_email(post, 'AuthInfo', properties, object_type, title)

    def test_send_password_custom_email_nsset(self):
        post = {
            "object_type": "nsset",
            "handle": "FOO",
            "confirmation_method": "signed_email",
            "send_to_0": "custom_email",
            "send_to_1": "foo@foo.off",
        }
        properties = {'handle': 'FOO', 'handleType': 'nsset', 'sendTo': 'custom_email', 'confirmMethod': 'signed_email',
                      'customEmail': 'foo@foo.off'}
        object_type = ObjectType_PR.nsset
        title = "Request summary"
        self._send_password_to_custom_email(post, 'AuthInfo', properties, object_type, title)

    def test_send_password_custom_email_keyset(self):
        post = {
            "object_type": "keyset",
            "handle": "FOO",
            "confirmation_method": "signed_email",
            "send_to_0": "custom_email",
            "send_to_1": "foo@foo.off",
        }
        properties = {'handle': 'FOO', 'handleType': 'keyset', 'sendTo': 'custom_email',
                      'confirmMethod': 'signed_email', 'customEmail': 'foo@foo.off'}
        object_type = ObjectType_PR.keyset
        title = "Request summary"
        self._send_password_to_custom_email(post, 'AuthInfo', properties, object_type, title)

    def test_send_password_email_in_registry_notarized_letter(self):
        post = {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "notarized_letter",
            "send_to_0": "email_in_registry",
        }
        response = self.client.post(reverse("webwhois:form_send_password"), post)
        self.assertEqual(response.context['form'].errors, {'__all__': [
            'Letter with officially verified signature can be sent only to the custom email. '
            'Please select "Send to custom email" and enter it.'
        ]})
        self.assertContains(response, escape(
                            'Letter with officially verified signature can be sent only to the custom email. '
                            'Please select "Send to custom email" and enter it.'))
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [])

        # Check logger
        self.assertEqual(self.test_logger.mock.mock_calls, [])

    def _send_password_notarized_letter_registry(self, object_name: str, object_type: str, title: str):
        post = {
            "object_type": object_name,
            "handle": "FOO",
            "confirmation_method": "notarized_letter",
            "send_to_0": "custom_email",
            "send_to_1": "foo@foo.off",
        }
        properties = {'handle': 'FOO', 'handleType': object_name, 'sendTo': 'custom_email',
                      'confirmMethod': 'notarized_letter', 'customEmail': 'foo@foo.off'}
        self._send_password_notarized_letter(post, 'AuthInfo', properties, object_type, title)
        public_response = SendPasswordResponse(object_name, 24, 'AuthInfo', 'FOO', 'foo@foo.off',
                                               ConfirmationMethod.NOTARIZED_LETTER)
        public_response.create_date = date(2017, 3, 8)
        self.assertEqual(cache.get(self.public_key), public_response)

    def test_send_password_notarized_letter_domain(self):
        title = "Request summary"
        object_type = ObjectType_PR.domain
        self._send_password_notarized_letter_registry('domain', object_type, title)

    def test_send_password_notarized_letter_contact(self):
        title = "Request summary"
        object_type = ObjectType_PR.contact
        self._send_password_notarized_letter_registry('contact', object_type, title)

    def test_send_password_notarized_letter_nsset(self):
        title = "Request summary"
        object_type = ObjectType_PR.nsset
        self._send_password_notarized_letter_registry('nsset', object_type, title)

    def test_send_password_notarized_letter_keyset(self):
        title = "Request summary"
        object_type = ObjectType_PR.keyset
        self._send_password_notarized_letter_registry('keyset', object_type, title)


@override_settings(TEMPLATES=TEMPLATES, USE_TZ=True)
class TestPersonalInfoFormView(SubmittedFormTestCase):
    """Test `PersonalInfoFormView` class."""

    def setUp(self):
        super().setUp()

        catcher = warnings.catch_warnings(record=True)
        self.addCleanup(catcher.__exit__)
        catcher.__enter__()

    def test_personal_info_email_in_registry(self):
        post = {"object_type": "contact", "handle": "CONTACT", "send_to_0": "email_in_registry"}
        PUBLIC_REQUEST.create_personal_info_request_registry_email.return_value = 24

        response = self.client.post(reverse("webwhois:form_personal_info"), post)

        path = reverse("webwhois:email_in_registry_response", kwargs={"public_key": self.public_key})
        self.assertRedirects(response, path)
        public_response = PersonalInfoResponse('contact', 24, 'PersonalInfo', 'CONTACT', None, None)
        public_response.create_date = date(2017, 3, 8)
        self.assertEqual(cache.get(self.public_key), public_response)
        self.assertEqual(PUBLIC_REQUEST.mock_calls,
                         [call.create_personal_info_request_registry_email(post['handle'], 42)])

        # Check logger
        properties = {'handle': 'CONTACT', 'handleType': 'contact', 'sendTo': 'email_in_registry'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.PERSONAL_INFO,
                                 PublicRequestsLogResult.SUCCESS, source_ip='127.0.0.1',
                                 input_properties=properties, references={'publicrequest': '24'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_personal_info_custom_email(self):
        post = {"object_type": "contact", "handle": "CONTACT", "confirmation_method": "signed_email",
                "send_to_0": "custom_email", "send_to_1": "kryten@example.cz"}
        PUBLIC_REQUEST.create_personal_info_request_non_registry_email.return_value = 24

        response = self.client.post(reverse("webwhois:form_personal_info"), post)

        path = reverse("webwhois:public_response", kwargs={"public_key": self.public_key})
        self.assertRedirects(response, path)
        public_response = PersonalInfoResponse('contact', 24, 'PersonalInfo', 'CONTACT', 'kryten@example.cz',
                                               ConfirmationMethod.SIGNED_EMAIL)
        public_response.create_date = date(2017, 3, 8)
        self.assertEqual(cache.get(self.public_key), public_response)
        calls = [call.create_personal_info_request_non_registry_email(post['handle'], 42, ConfirmedBy.signed_email,
                                                                      'kryten@example.cz')]
        self.assertEqual(PUBLIC_REQUEST.mock_calls, calls)

        # Check logger
        properties = {'handle': 'CONTACT', 'handleType': 'contact', 'sendTo': 'custom_email',
                      'confirmMethod': 'signed_email', 'customEmail': 'kryten@example.cz'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.PERSONAL_INFO,
                                 PublicRequestsLogResult.SUCCESS, source_ip='127.0.0.1',
                                 input_properties=properties, references={'publicrequest': '24'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_personal_info_notarized_letter(self):
        post = {"object_type": "contact", "handle": "CONTACT", "confirmation_method": "notarized_letter",
                "send_to_0": "custom_email", "send_to_1": "kryten@example.cz"}
        PUBLIC_REQUEST.create_personal_info_request_non_registry_email.return_value = 24

        response = self.client.post(reverse("webwhois:form_personal_info"), post)

        path = reverse("webwhois:public_response", kwargs={"public_key": self.public_key})
        self.assertRedirects(response, path)
        public_response = PersonalInfoResponse('contact', 24, 'PersonalInfo', 'CONTACT', 'kryten@example.cz',
                                               ConfirmationMethod.NOTARIZED_LETTER)
        public_response.create_date = date(2017, 3, 8)
        self.assertEqual(cache.get(self.public_key), public_response)

        calls = [call.create_personal_info_request_non_registry_email(post['handle'], 42, ConfirmedBy.notarized_letter,
                                                                      'kryten@example.cz')]
        self.assertEqual(PUBLIC_REQUEST.mock_calls, calls)

        # Check logger
        properties = {'handle': 'CONTACT', 'handleType': 'contact', 'sendTo': 'custom_email',
                      'confirmMethod': 'notarized_letter', 'customEmail': 'kryten@example.cz'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.PERSONAL_INFO,
                                 PublicRequestsLogResult.SUCCESS, source_ip='127.0.0.1',
                                 input_properties=properties, references={'publicrequest': '24'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def _test_personal_info_error(self, exception_code: str, form_errors: Dict) -> None:
        post = {"handle": "foo.cz", "send_to_0": "email_in_registry"}

        response = self.client.post(reverse("webwhois:form_personal_info"), post)

        self.assertContains(response, 'Request to send personal information')
        self.assertEqual(response.context['form'].errors, form_errors)
        self.assertEqual(PUBLIC_REQUEST.mock_calls,
                         [call.create_personal_info_request_registry_email('foo.cz', 42)])

        # Check logger
        properties = {'handle': 'foo.cz', 'handleType': 'contact', 'sendTo': 'email_in_registry'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.PERSONAL_INFO,
                                 PublicRequestsLogResult.FAIL, source_ip='127.0.0.1',
                                 input_properties=properties, properties={'reason': exception_code})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_personal_info_object_not_found(self):
        PUBLIC_REQUEST.create_personal_info_request_registry_email.side_effect = OBJECT_NOT_FOUND
        self._test_personal_info_error(
            'OBJECT_NOT_FOUND',
            {'handle': ['Object not found. Check that you have correctly entered the contact handle.']})

    def test_personal_info_invalid_email(self):
        PUBLIC_REQUEST.create_personal_info_request_registry_email.side_effect = INVALID_EMAIL
        self._test_personal_info_error(
            'INVALID_EMAIL',
            {'send_to': ['The email was not found or the address is not valid.']})


@override_settings(TEMPLATES=TEMPLATES, USE_TZ=True)
class TestBlockUnblockForm(SubmittedFormTestCase):

    def setUp(self):
        super().setUp()

        catcher = warnings.catch_warnings(record=True)
        self.addCleanup(catcher.__exit__)
        catcher.__enter__()

    def _block_unblock(
            self, block_action: str, url_name: str, object_name: str, confirmation_method: str, lock_type: str,
            action_name: str, object_type: str, signed_type: str, block_type: str, title: str) -> None:
        post = {
            "handle": "FOO",
            "object_type": object_name,
            "confirmation_method": confirmation_method,
            "lock_type": lock_type,
        }
        PUBLIC_REQUEST.create_block_unblock_request.return_value = 24
        response = self.client.post(reverse(url_name), post, follow=True)
        self.assertRedirects(response, reverse("webwhois:public_response", kwargs={"public_key": self.public_key}))
        self.assertContains(response, title)
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_block_unblock_request(object_type, 'FOO', 42, signed_type, block_type)
        ])
        public_response = BlockResponse(object_name, 24, action_name, 'FOO', block_action, lock_type,
                                        confirmation_method)
        self.assertEqual(cache.get(self.public_key), public_response)

        # Check logger
        properties = {'handle': 'FOO', 'handleType': object_name, 'confirmMethod': confirmation_method}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, action_name,
                                 PublicRequestsLogResult.SUCCESS, source_ip='127.0.0.1',
                                 input_properties=properties, references={'publicrequest': '24'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def _block_transfer_signed_email(self, object_name: str, object_type: str, title: str) -> None:
        lock_type = "transfer"
        action_name = "BlockTransfer"
        block_type = LockRequestType.block_transfer
        confirmation_method = "signed_email"
        signed_type = ConfirmedBy.signed_email
        self._block_unblock("block", "webwhois:form_block_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title)

    def _block_all_signed_email(self, object_name: str, object_type: str, title: str) -> None:
        lock_type = "all"
        action_name = "BlockChanges"
        block_type = LockRequestType.block_transfer_and_update
        confirmation_method = "signed_email"
        signed_type = ConfirmedBy.signed_email
        self._block_unblock("block", "webwhois:form_block_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title)

    def _unblock_transfer_signed_email(self, object_name: str, object_type: str, title: str) -> None:
        lock_type = "transfer"
        action_name = "UnblockTransfer"
        block_type = LockRequestType.unblock_transfer
        confirmation_method = "signed_email"
        signed_type = ConfirmedBy.signed_email
        self._block_unblock("unblock", "webwhois:form_unblock_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title)

    def _unblock_all_signed_email(self, object_name: str, object_type: str, title: str) -> None:
        lock_type = "all"
        action_name = "UnblockChanges"
        block_type = LockRequestType.unblock_transfer_and_update
        confirmation_method = "signed_email"
        signed_type = ConfirmedBy.signed_email
        self._block_unblock("unblock", "webwhois:form_unblock_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title)

    def test_block_transfer_signed_email_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = "Request summary"
        self._block_transfer_signed_email(object_name, object_type, title)

    def test_block_transfer_signed_email_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = "Request summary"
        self._block_transfer_signed_email(object_name, object_type, title)

    def test_block_transfer_signed_email_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = "Request summary"
        self._block_transfer_signed_email(object_name, object_type, title)

    def test_block_transfer_signed_email_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = "Request summary"
        self._block_transfer_signed_email(object_name, object_type, title)

    def test_unblock_transfer_signed_email_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = "Request summary"
        self._unblock_transfer_signed_email(object_name, object_type, title)

    def test_unblock_transfer_signed_email_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = "Request summary"
        self._unblock_transfer_signed_email(object_name, object_type, title)

    def test_unblock_transfer_signed_email_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = "Request summary"
        self._unblock_transfer_signed_email(object_name, object_type, title)

    def test_unblock_transfer_signed_email_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = "Request summary"
        self._unblock_transfer_signed_email(object_name, object_type, title)

    def test_block_all_signed_email_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = "Request summary"
        self._block_all_signed_email(object_name, object_type, title)

    def test_block_all_signed_email_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = "Request summary"
        self._block_all_signed_email(object_name, object_type, title)

    def test_block_all_signed_email_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = "Request summary"
        self._block_all_signed_email(object_name, object_type, title)

    def test_block_all_signed_email_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = "Request summary"
        self._block_all_signed_email(object_name, object_type, title)

    def test_unblock_all_signed_email_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = "Request summary"
        self._unblock_all_signed_email(object_name, object_type, title)

    def test_unblock_all_signed_email_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = "Request summary"
        self._unblock_all_signed_email(object_name, object_type, title)

    def test_unblock_all_signed_email_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = "Request summary"
        self._unblock_all_signed_email(object_name, object_type, title)

    def test_unblock_all_signed_email_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = "Request summary"
        self._unblock_all_signed_email(object_name, object_type, title)

    def _block_transfer_notarized_letter(self, object_name, object_type, title):
        lock_type = "transfer"
        action_name = "BlockTransfer"
        block_type = LockRequestType.block_transfer
        confirmation_method = "notarized_letter"
        signed_type = ConfirmedBy.notarized_letter
        self._block_unblock("block", "webwhois:form_block_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title)

    def _unblock_transfer_notarized_letter(self, object_name, object_type, title):
        lock_type = "transfer"
        action_name = "UnblockTransfer"
        block_type = LockRequestType.unblock_transfer
        confirmation_method = "notarized_letter"
        signed_type = ConfirmedBy.notarized_letter
        self._block_unblock("unblock", "webwhois:form_unblock_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title)

    def _block_all_notarized_letter(self, object_name, object_type, title):
        lock_type = "all"
        action_name = "BlockChanges"
        block_type = LockRequestType.block_transfer_and_update
        confirmation_method = "notarized_letter"
        signed_type = ConfirmedBy.notarized_letter
        self._block_unblock("block", "webwhois:form_block_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title)

    def _unblock_all_notarized_letter(self, object_name, object_type, title):
        lock_type = "all"
        action_name = "UnblockChanges"
        block_type = LockRequestType.unblock_transfer_and_update
        confirmation_method = "notarized_letter"
        signed_type = ConfirmedBy.notarized_letter
        self._block_unblock("unblock", "webwhois:form_unblock_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title)

    def test_block_transfer_notarized_letter_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = "Request summary"
        self._block_transfer_notarized_letter(object_name, object_type, title)

    def test_block_transfer_notarized_letter_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = "Request summary"
        self._block_transfer_notarized_letter(object_name, object_type, title)

    def test_block_transfer_notarized_letter_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = "Request summary"
        self._block_transfer_notarized_letter(object_name, object_type, title)

    def test_block_transfer_notarized_letter_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = "Request summary"
        self._block_transfer_notarized_letter(object_name, object_type, title)

    def test_unblock_transfer_notarized_letter_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = "Request summary"
        self._unblock_transfer_notarized_letter(object_name, object_type, title)

    def test_unblock_transfer_notarized_letter_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = "Request summary"
        self._unblock_transfer_notarized_letter(object_name, object_type, title)

    def test_unblock_transfer_notarized_letter_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = "Request summary"
        self._unblock_transfer_notarized_letter(object_name, object_type, title)

    def test_unblock_transfer_notarized_letter_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = "Request summary"
        self._unblock_transfer_notarized_letter(object_name, object_type, title)

    def test_block_all_notarized_letter_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = "Request summary"
        self._block_all_notarized_letter(object_name, object_type, title)

    def test_block_all_notarized_letter_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = "Request summary"
        self._block_all_notarized_letter(object_name, object_type, title)

    def test_block_all_notarized_letter_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = "Request summary"
        self._block_all_notarized_letter(object_name, object_type, title)

    def test_block_all_notarized_letter_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = "Request summary"
        self._block_all_notarized_letter(object_name, object_type, title)

    def test_unblock_all_notarized_letter_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = "Request summary"
        self._unblock_all_notarized_letter(object_name, object_type, title)

    def test_unblock_all_notarized_letter_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = "Request summary"
        self._unblock_all_notarized_letter(object_name, object_type, title)

    def test_unblock_all_notarized_letter_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = "Request summary"
        self._unblock_all_notarized_letter(object_name, object_type, title)

    def test_unblock_all_notarized_letter_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = "Request summary"
        self._unblock_all_notarized_letter(object_name, object_type, title)

    def _assert_create_block_unblock_exception(self, exception_code, form_error_message):
        post = {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "lock_type": "transfer",
        }
        response = self.client.post(reverse("webwhois:form_block_object"), post)
        self.assertEqual(response.context['form'].errors, {'handle': [form_error_message]})
        self.assertContains(response, form_error_message)
        object_type = ObjectType_PR.domain
        signed_email = ConfirmedBy.signed_email
        block_transfer = LockRequestType.block_transfer
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_block_unblock_request(object_type, 'foo.cz', 42, signed_email, block_transfer)
        ])

        # Check logger
        properties = {'handle': 'foo.cz', 'handleType': 'domain', 'confirmMethod': 'signed_email'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.BLOCK_TRANSFER,
                                 PublicRequestsLogResult.FAIL, source_ip='127.0.0.1',
                                 input_properties=properties, properties={'reason': exception_code})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_block_object_not_found(self):
        PUBLIC_REQUEST.create_block_unblock_request.side_effect = OBJECT_NOT_FOUND
        self._assert_create_block_unblock_exception('OBJECT_NOT_FOUND', 'Object not found. Check that you have'
                                                    ' correctly entered the Object type and Handle.')

    def test_block_object_already_blocked(self):
        PUBLIC_REQUEST.create_block_unblock_request.side_effect = OBJECT_ALREADY_BLOCKED
        self._assert_create_block_unblock_exception('OBJECT_ALREADY_BLOCKED', 'This object is already blocked. '
                                                    'The request can not be accepted.')

    def test_unblock_object_not_blocked(self):
        PUBLIC_REQUEST.create_block_unblock_request.side_effect = OBJECT_NOT_BLOCKED
        self._assert_create_block_unblock_exception('OBJECT_NOT_BLOCKED', 'This object is not blocked. '
                                                    'The request can not be accepted.')

    def test_block_object_has_different_block(self):
        PUBLIC_REQUEST.create_block_unblock_request.side_effect = HAS_DIFFERENT_BLOCK
        self._assert_create_block_unblock_exception('HAS_DIFFERENT_BLOCK', 'This object has another active blocking. '
                                                    'The request can not be accepted.')

    def test_block_object_operation_prohibited(self):
        PUBLIC_REQUEST.create_block_unblock_request.side_effect = OPERATION_PROHIBITED
        self._assert_create_block_unblock_exception('OPERATION_PROHIBITED', 'Operation for this object is prohibited. '
                                                    'The request can not be accepted.')


class TestException(Exception):
    "Test exception"


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
                   ROOT_URLCONF='webwhois.tests.urls')
class TestNotarizedLetterPdf(SimpleTestCase):

    public_key = "1234567890123456789012345678901234567890123456789012345678901234"

    def setUp(self):
        apply_patch(self, patch.object(PUBLIC_REQUEST, 'client', spec=('create_public_request_pdf', )))

        self.test_logger = TestLoggerClient()
        log_patcher = patch('webwhois.utils.corba_wrapper.PUBLIC_REQUESTS_LOGGER.client', new=self.test_logger)
        self.addCleanup(log_patcher.stop)
        log_patcher.start()

        self.catcher = warnings.catch_warnings(record=True)
        self.addCleanup(self.catcher.__exit__)
        self.catcher.__enter__()

    def tearDown(self):
        cache.clear()

    def test_download(self):
        cache.set(self.public_key, SendPasswordResponse('contact', 42, 'AuthInfo', 'FOO', None, None))
        PUBLIC_REQUEST.create_public_request_pdf.return_value = "PDF content..."
        response = self.client.get(reverse("webwhois:notarized_letter_serve_pdf",
                                           kwargs={"public_key": self.public_key}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'], 'attachment; filename="notarized-letter-en.pdf"')
        self.assertEqual(response.content, "PDF content...".encode())
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_public_request_pdf(42, Language.en)
        ])

        # Check logger
        properties = {'handle': 'FOO', 'objectType': 'contact', 'pdfLangCode': 'en', 'documentType': 'AuthInfo'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.NOTARIZED_LETTER_PDF,
                                 PublicRequestsLogResult.SUCCESS, source_ip='127.0.0.1',
                                 input_properties=properties, references={'publicrequest': '42'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_no_data(self):
        response = self.client.get(reverse("webwhois:notarized_letter_serve_pdf",
                                           kwargs={"public_key": self.public_key}))
        self.assertIsInstance(response, HttpResponseNotFound)
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [])
        self.assertEqual(self.test_logger.mock.mock_calls, [])

    def test_download_custom_email(self):
        cache.set(self.public_key, SendPasswordResponse('contact', 42, 'AuthInfo', 'FOO', 'foo@foo.off', None))
        PUBLIC_REQUEST.create_public_request_pdf.return_value = "PDF content..."
        response = self.client.get(reverse("webwhois:notarized_letter_serve_pdf",
                                           kwargs={"public_key": self.public_key}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'], 'attachment; filename="notarized-letter-en.pdf"')
        self.assertEqual(response.content, "PDF content...".encode())
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_public_request_pdf(42, Language.en)
        ])

        # Check logger
        properties = {'handle': 'FOO', 'objectType': 'contact', 'pdfLangCode': 'en', 'documentType': 'AuthInfo',
                      'customEmail': 'foo@foo.off'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.NOTARIZED_LETTER_PDF,
                                 PublicRequestsLogResult.SUCCESS, source_ip='127.0.0.1',
                                 input_properties=properties, references={'publicrequest': '42'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_object_not_found(self):
        cache.set(self.public_key, SendPasswordResponse('contact', 42, 'AuthInfo', 'FOO', None, None))
        PUBLIC_REQUEST.create_public_request_pdf.side_effect = OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:notarized_letter_serve_pdf",
                                           kwargs={"public_key": self.public_key}))
        self.assertIsInstance(response, HttpResponseNotFound)
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_public_request_pdf(42, Language.en)
        ])

        # Check logger
        properties = {'handle': 'FOO', 'objectType': 'contact', 'pdfLangCode': 'en', 'documentType': 'AuthInfo'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.NOTARIZED_LETTER_PDF,
                                 PublicRequestsLogResult.FAIL, source_ip='127.0.0.1',
                                 input_properties=properties, properties={'reason': 'OBJECT_NOT_FOUND'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_unexpected_exception(self):
        cache.set(self.public_key, SendPasswordResponse('contact', 42, 'AuthInfo', 'FOO', None))
        PUBLIC_REQUEST.create_public_request_pdf.side_effect = TestException
        with self.assertRaises(TestException):
            self.client.get(reverse("webwhois:notarized_letter_serve_pdf", kwargs={"public_key": self.public_key}))
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_public_request_pdf(42, Language.en)
        ])

        # Check logger
        properties = {'handle': 'FOO', 'objectType': 'contact', 'pdfLangCode': 'en', 'documentType': 'AuthInfo'}
        log_entry = TestLogEntry(PUBLIC_REQUESTS_LOGGER_SERVICE, PublicRequestsLogEntryType.NOTARIZED_LETTER_PDF,
                                 PublicRequestsLogResult.ERROR, source_ip='127.0.0.1',
                                 input_properties=properties, properties={'exception': 'TestException'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
                   ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class PublicResponseViewTest(SimpleTestCase):

    public_key = "Gazpacho!"

    def tearDown(self):
        cache.clear()

    def test_get(self):
        public_response = SendPasswordResponse('contact', 42, PublicRequestsLogEntryType.AUTH_INFO, 'KRYTEN',
                                               'kryten@example.org', ConfirmationMethod.SIGNED_EMAIL)
        public_response.create_date = date(1988, 9, 6)
        cache.set(self.public_key, public_response)

        response = self.client.get(reverse("webwhois:public_response", kwargs={"public_key": self.public_key}))

        self.assertContains(response, 'request')
        self.assertEqual(response.context['public_response'], public_response)
        self.assertEqual(response.context['public_key'], self.public_key)

    def test_no_data(self):
        response = self.client.get(reverse("webwhois:public_response", kwargs={"public_key": self.public_key}))

        self.assertRedirects(response, reverse("webwhois:response_not_found", kwargs={"public_key": self.public_key}))


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
                   ROOT_URLCONF='webwhois.tests.urls')
class PublicResponsePdfViewTest(SimpleTestCase):

    public_key = "Gazpacho!"

    def setUp(self):
        patcher = patch('webwhois.views.public_request.SECRETARY_CLIENT', autospec=True)
        self.addCleanup(patcher.stop)
        self.secretary_mock = patcher.start()

    def tearDown(self):
        cache.clear()

    def _test_pdf(self, public_response: PublicResponse, template: str, context: Dict[str, Any]) -> None:
        self.secretary_mock.render_pdf.return_value = b'Quagaars!'
        cache.set(self.public_key, public_response)

        response = self.client.get(reverse("webwhois:public_response_pdf", kwargs={"public_key": self.public_key}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'], 'attachment; filename="public-request-KRYTEN.pdf"')
        self.assertEqual(response.content, b'Quagaars!')
        self.assertEqual(self.secretary_mock.mock_calls, [call.render_pdf(template, context)])

    def test_send_password(self):
        public_response = SendPasswordResponse('contact', 42, PublicRequestsLogEntryType.AUTH_INFO, 'KRYTEN',
                                               'kryten@example.org', ConfirmationMethod.SIGNED_EMAIL)
        public_response.create_date = date(1988, 9, 6)
        context = {'type': 'contact', 'identifier': 42, 'handle': 'KRYTEN', 'date': '1988-09-06',
                   'email': 'kryten@example.org', 'block_type': None}
        self._test_pdf(public_response, 'public-request-auth-info-en-us.html', context)

    def test_personal_info(self):
        public_response = PersonalInfoResponse('contact', 42, PublicRequestsLogEntryType.PERSONAL_INFO, 'KRYTEN',
                                               'kryten@example.org', ConfirmationMethod.SIGNED_EMAIL)
        public_response.create_date = date(1988, 9, 6)
        context = {'type': 'contact', 'identifier': 42, 'handle': 'KRYTEN', 'date': '1988-09-06',
                   'email': 'kryten@example.org', 'block_type': None}
        self._test_pdf(public_response, 'public-request-personal-info-en-us.html', context)

    def test_block_all(self):
        public_response = BlockResponse('contact', 42, PublicRequestsLogEntryType.BLOCK_CHANGES, 'KRYTEN', None,
                                        sentinel.block_type, ConfirmationMethod.SIGNED_EMAIL)
        public_response.create_date = date(1988, 9, 6)
        context = {'type': 'contact', 'identifier': 42, 'handle': 'KRYTEN', 'date': '1988-09-06', 'email': None,
                   'block_type': sentinel.block_type}
        self._test_pdf(public_response, 'public-request-block-en-us.html', context)

    def test_no_data(self):
        response = self.client.get(reverse("webwhois:public_response_pdf", kwargs={"public_key": self.public_key}))

        self.assertContains(response, 'Not Found', status_code=404)
        self.assertEqual(self.secretary_mock.mock_calls, [])


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
                   ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestResponseErrorMessage(SimpleTestCase):

    public_key = "1234567890123456789012345678901234567890123456789012345678901234"

    def setUp(self):
        catcher = warnings.catch_warnings(record=True)
        self.addCleanup(catcher.__exit__)
        catcher.__enter__()

    def _assert_response(self, path):
        response = self.client.get(path, follow=True)
        self.assertContains(response,
                            'Sorry, but the request does not exist or has expired. Please enter a new one.',
                            html=True)
        self.assertRedirects(response, reverse("webwhois:response_not_found", kwargs={"public_key": self.public_key}))

    def test_email_in_registry_response(self):
        self._assert_response(reverse("webwhois:email_in_registry_response", kwargs={"public_key": self.public_key}))

    def test_custom_email_response(self):
        self._assert_response(reverse("webwhois:custom_email_response", kwargs={"public_key": self.public_key}))

    def test_notarized_letter_response(self):
        self._assert_response(reverse("webwhois:notarized_letter_response", kwargs={"public_key": self.public_key}))
