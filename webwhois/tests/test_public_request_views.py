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
from datetime import date
from unittest.mock import call, patch

from django.core.cache import cache
from django.http import HttpResponseNotFound
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils.html import escape
from fred_idl.Registry.PublicRequest import HAS_DIFFERENT_BLOCK, INVALID_EMAIL, OBJECT_ALREADY_BLOCKED, \
    OBJECT_NOT_BLOCKED, OBJECT_NOT_FOUND, OBJECT_TRANSFER_PROHIBITED, OPERATION_PROHIBITED, ConfirmedBy, Language, \
    LockRequestType, ObjectType_PR

from webwhois.forms.public_request import ConfirmationMethod
from webwhois.forms.widgets import DeliveryType
from webwhois.tests.utils import TEMPLATES, apply_patch
from webwhois.utils import PUBLIC_REQUEST
from webwhois.utils.public_response import BlockResponse, PersonalInfoResponse, PublicResponse, SendPasswordResponse


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
        self.LOGGER = apply_patch(self, patch("webwhois.views.logger_mixin.LOGGER"))
        self.LOGGER.create_request.return_value.request_id = 42
        self.LOGGER.create_request.return_value.result = 'Error'
        self.LOGGER.create_request.return_value.request_type = 'AuthInfo'
        apply_patch(self, patch("webwhois.views.public_request_mixin.LOGGER", self.LOGGER))
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

    def _send_password_email_in_registry(self, post, action_name, properties, object_type, title, message):
        PUBLIC_REQUEST.create_authinfo_request_registry_email.return_value = 24
        response = self.client.post(reverse("webwhois:form_send_password"), post, follow=True)
        path = reverse("webwhois:email_in_registry_response", kwargs={"public_key": self.public_key})
        self.assertRedirects(response, path)
        self.assertContains(response, title)
        self.assertContains(response, message)
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_authinfo_request_registry_email(object_type, post['handle'], 42)
        ])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'AuthInfo', properties=properties),
            call().close(properties=[], references=[('publicrequest', 24)])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')

    def test_send_password_email_in_registry_domain(self):
        post = {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        }
        properties = [
            ('handle', 'foo.cz'),
            ('handleType', 'domain'),
            ('sendTo', 'email_in_registry'),
            ('confirmMethod', 'signed_email'),
        ]
        object_type = ObjectType_PR.domain
        title = "Request to send a password (authinfo) for transfer domain name foo.cz"
        message = "We received successfully your request for a password to change the domain <strong>foo.cz</strong> " \
                  "sponsoring registrar. An email with the password will be sent to the email address of domain " \
                  "holder and admin contacts."
        self._send_password_email_in_registry(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_email_in_registry_contact(self):
        post = {
            "object_type": "contact",
            "handle": "CONTACT",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        }
        properties = [
            ('handle', 'CONTACT'),
            ('handleType', 'contact'),
            ('sendTo', 'email_in_registry'),
            ('confirmMethod', 'signed_email'),
        ]
        object_type = ObjectType_PR.contact
        title = "Request to send a password (authinfo) for transfer contact CONTACT"
        message = "We received successfully your request for a password to change the contact " \
                  "<strong>CONTACT</strong> sponsoring registrar. An email with the password will be sent to " \
                  "the email address from the registry."
        self._send_password_email_in_registry(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_email_in_registry_nsset(self):
        post = {
            "object_type": "nsset",
            "handle": "NSSET",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        }
        properties = [
            ('handle', 'NSSET'),
            ('handleType', 'nsset'),
            ('sendTo', 'email_in_registry'),
            ('confirmMethod', 'signed_email'),
        ]
        object_type = ObjectType_PR.nsset
        title = "Request to send a password (authinfo) for transfer nameserver set NSSET"
        message = "We received successfully your request for a password to change the nameserver set " \
                  "<strong>NSSET</strong> sponsoring registrar. An email with the password will be sent to the email " \
                  "addresses of the nameserver set's technical contacts."
        self._send_password_email_in_registry(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_email_in_registry_keyset(self):
        post = {
            "object_type": "keyset",
            "handle": "KEYSET",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        }
        properties = [
            ('handle', 'KEYSET'),
            ('handleType', 'keyset'),
            ('sendTo', 'email_in_registry'),
            ('confirmMethod', 'signed_email'),
        ]
        object_type = ObjectType_PR.keyset
        title = "Request to send a password (authinfo) for transfer keyset KEYSET"
        message = "We received successfully your request for a password to change the keyset " \
                  "<strong>KEYSET</strong> sponsoring registrar. An email with the password will be sent to " \
                  "the email addresses of the keyset's technical contacts."
        self._send_password_email_in_registry(post, 'AuthInfo', properties, object_type, title, message)

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
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'AuthInfo', properties=[
                ('handle', 'foo.cz'),
                ('handleType', 'domain'),
                ('sendTo', 'email_in_registry'),
                ('confirmMethod', 'signed_email'),
            ]),
            call().close(properties=[('reason', exception_code)], references=[])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Fail')

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
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'AuthInfo', properties=[
                ('handle', 'foo.cz'),
                ('handleType', 'domain'),
                ('sendTo', 'custom_email'),
                ('confirmMethod', 'signed_email'),
                ('customEmail', 'foo@foo.off')]),
            call().close(properties=[('reason', 'INVALID_EMAIL')], references=[])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Fail')

    def _send_password_confirm_method(self, confirm_method, post, action_name, properties, object_type, title, message):
        PUBLIC_REQUEST.create_authinfo_request_non_registry_email.return_value = 24
        response = self.client.post(reverse("webwhois:form_send_password"), post, follow=True)
        if post['confirmation_method'] == 'signed_email':
            url_name = "webwhois:custom_email_response"
        else:
            url_name = "webwhois:notarized_letter_response"
        self.assertRedirects(response, reverse(url_name, kwargs={"public_key": self.public_key}))
        self.assertContains(response, title)
        self.assertContains(response, message)
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_authinfo_request_non_registry_email(object_type, post['handle'], 42, confirm_method,
                                                            'foo@foo.off')
        ])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'AuthInfo', properties=properties),
            call().close(properties=[], references=[('publicrequest', 24)])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')

    def _send_password_to_custom_email(self, post, action_name, properties, object_type, title, message):
        conftype = ConfirmedBy.signed_email
        self._send_password_confirm_method(conftype, post, action_name, properties, object_type, title, message)

    def _send_password_notarized_letter(self, post, action_name, properties, object_type, title, message):
        conftype = ConfirmedBy.notarized_letter
        self._send_password_confirm_method(conftype, post, action_name, properties, object_type, title, message)

    def test_send_password_custom_email_domain(self):
        post = {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to_0": "custom_email",
            "send_to_1": "foo@foo.off",
        }
        properties = [
            ('handle', 'foo.cz'),
            ('handleType', 'domain'),
            ('sendTo', 'custom_email'),
            ('confirmMethod', 'signed_email'),
            ('customEmail', 'foo@foo.off'),
        ]
        object_type = ObjectType_PR.domain
        title = "Request to send a password (authinfo) for transfer domain name foo.cz"
        message = "I hereby confirm my request to get the password for domain name foo.cz, submitted through " \
                  "the web form at http://testserver/whois/send-password/ on March 8, 2017, assigned id number 24. " \
                  "Please send the password to foo@foo.off."
        self._send_password_to_custom_email(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_custom_email_contact(self):
        post = {
            "object_type": "contact",
            "handle": "FOO",
            "confirmation_method": "signed_email",
            "send_to_0": "custom_email",
            "send_to_1": "foo@foo.off",
        }
        properties = [
            ('handle', 'FOO'),
            ('handleType', 'contact'),
            ('sendTo', 'custom_email'),
            ('confirmMethod', 'signed_email'),
            ('customEmail', 'foo@foo.off'),
        ]
        object_type = ObjectType_PR.contact
        title = "Request to send a password (authinfo) for transfer contact FOO"
        message = "I hereby confirm my request to get the password for contact FOO, submitted through " \
                  "the web form at http://testserver/whois/send-password/ on March 8, 2017, assigned id number 24. " \
                  "Please send the password to foo@foo.off."
        self._send_password_to_custom_email(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_custom_email_nsset(self):
        post = {
            "object_type": "nsset",
            "handle": "FOO",
            "confirmation_method": "signed_email",
            "send_to_0": "custom_email",
            "send_to_1": "foo@foo.off",
        }
        properties = [
            ('handle', 'FOO'),
            ('handleType', 'nsset'),
            ('sendTo', 'custom_email'),
            ('confirmMethod', 'signed_email'),
            ('customEmail', 'foo@foo.off'),
        ]
        object_type = ObjectType_PR.nsset
        title = "Request to send a password (authinfo) for transfer nameserver set FOO"
        message = "I hereby confirm my request to get the password for nameserver set FOO, submitted through " \
                  "the web form at http://testserver/whois/send-password/ on March 8, 2017, assigned id number 24. " \
                  "Please send the password to foo@foo.off."
        self._send_password_to_custom_email(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_custom_email_keyset(self):
        post = {
            "object_type": "keyset",
            "handle": "FOO",
            "confirmation_method": "signed_email",
            "send_to_0": "custom_email",
            "send_to_1": "foo@foo.off",
        }
        properties = [
            ('handle', 'FOO'),
            ('handleType', 'keyset'),
            ('sendTo', 'custom_email'),
            ('confirmMethod', 'signed_email'),
            ('customEmail', 'foo@foo.off'),
        ]
        object_type = ObjectType_PR.keyset
        title = "Request to send a password (authinfo) for transfer keyset FOO"
        message = "I hereby confirm my request to get the password for keyset FOO, submitted through " \
                  "the web form at http://testserver/whois/send-password/ on March 8, 2017, assigned id number 24. " \
                  "Please send the password to foo@foo.off."
        self._send_password_to_custom_email(post, 'AuthInfo', properties, object_type, title, message)

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
        self.assertEqual(self.LOGGER.create_request.mock_calls, [])

    def _send_password_notarized_letter_registry(self, object_name, object_type, title):
        post = {
            "object_type": object_name,
            "handle": "FOO",
            "confirmation_method": "notarized_letter",
            "send_to_0": "custom_email",
            "send_to_1": "foo@foo.off",
        }
        properties = [
            ('handle', 'FOO'),
            ('handleType', object_name),
            ('sendTo', 'custom_email'),
            ('confirmMethod', 'notarized_letter'),
            ('customEmail', 'foo@foo.off'),
        ]
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Password (authinfo) request</a> ' \
                  '(PDF)' % self.public_key
        self._send_password_notarized_letter(post, 'AuthInfo', properties, object_type, title, message)
        public_response = SendPasswordResponse(object_name, 24, 'AuthInfo', 'FOO', 'foo@foo.off',
                                               ConfirmationMethod.NOTARIZED_LETTER)
        public_response.create_date = date(2017, 3, 8)
        self.assertEqual(cache.get(self.public_key), public_response)

    def test_send_password_notarized_letter_domain(self):
        title = "Request to send a password (authinfo) for transfer domain name FOO"
        object_type = ObjectType_PR.domain
        self._send_password_notarized_letter_registry('domain', object_type, title)

    def test_send_password_notarized_letter_contact(self):
        title = "Request to send a password (authinfo) for transfer contact FOO"
        object_type = ObjectType_PR.contact
        self._send_password_notarized_letter_registry('contact', object_type, title)

    def test_send_password_notarized_letter_nsset(self):
        title = "Request to send a password (authinfo) for transfer nameserver set FOO"
        object_type = ObjectType_PR.nsset
        self._send_password_notarized_letter_registry('nsset', object_type, title)

    def test_send_password_notarized_letter_keyset(self):
        title = "Request to send a password (authinfo) for transfer keyset FOO"
        object_type = ObjectType_PR.keyset
        self._send_password_notarized_letter_registry('keyset', object_type, title)


@override_settings(TEMPLATES=TEMPLATES, USE_TZ=True)
class TestPersonalInfoFormView(SubmittedFormTestCase):
    """Test `PersonalInfoFormView` class."""

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
        properties = [('handle', 'CONTACT'), ('handleType', 'contact'), ('sendTo', 'email_in_registry')]
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'PersonalInfo', properties=properties),
            call().close(properties=[], references=[('publicrequest', 24)])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')

    def test_personal_info_custom_email(self):
        post = {"object_type": "contact", "handle": "CONTACT", "confirmation_method": "signed_email",
                "send_to_0": "custom_email", "send_to_1": "kryten@example.cz"}
        PUBLIC_REQUEST.create_personal_info_request_non_registry_email.return_value = 24

        response = self.client.post(reverse("webwhois:form_personal_info"), post)

        path = reverse("webwhois:custom_email_response", kwargs={"public_key": self.public_key})
        self.assertRedirects(response, path)
        public_response = PersonalInfoResponse('contact', 24, 'PersonalInfo', 'CONTACT', 'kryten@example.cz',
                                               ConfirmationMethod.SIGNED_EMAIL)
        public_response.create_date = date(2017, 3, 8)
        self.assertEqual(cache.get(self.public_key), public_response)
        calls = [call.create_personal_info_request_non_registry_email(post['handle'], 42, ConfirmedBy.signed_email,
                                                                      'kryten@example.cz')]
        self.assertEqual(PUBLIC_REQUEST.mock_calls, calls)
        properties = [('handle', 'CONTACT'), ('handleType', 'contact'), ('sendTo', 'custom_email'),
                      ('confirmMethod', 'signed_email'), ('customEmail', 'kryten@example.cz')]
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'PersonalInfo', properties=properties),
            call().close(properties=[], references=[('publicrequest', 24)])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')

    def test_personal_info_notarized_letter(self):
        post = {"object_type": "contact", "handle": "CONTACT", "confirmation_method": "notarized_letter",
                "send_to_0": "custom_email", "send_to_1": "kryten@example.cz"}
        PUBLIC_REQUEST.create_personal_info_request_non_registry_email.return_value = 24

        response = self.client.post(reverse("webwhois:form_personal_info"), post)

        path = reverse("webwhois:notarized_letter_response", kwargs={"public_key": self.public_key})
        self.assertRedirects(response, path)
        public_response = PersonalInfoResponse('contact', 24, 'PersonalInfo', 'CONTACT', 'kryten@example.cz',
                                               ConfirmationMethod.NOTARIZED_LETTER)
        public_response.create_date = date(2017, 3, 8)
        self.assertEqual(cache.get(self.public_key), public_response)

        calls = [call.create_personal_info_request_non_registry_email(post['handle'], 42, ConfirmedBy.notarized_letter,
                                                                      'kryten@example.cz')]
        self.assertEqual(PUBLIC_REQUEST.mock_calls, calls)
        properties = [('handle', 'CONTACT'), ('handleType', 'contact'), ('sendTo', 'custom_email'),
                      ('confirmMethod', 'notarized_letter'), ('customEmail', 'kryten@example.cz')]
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'PersonalInfo', properties=properties),
            call().close(properties=[], references=[('publicrequest', 24)])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')

    def _test_personal_info_error(self, exception_code, form_errors):
        post = {"object_type": "domain", "handle": "foo.cz", "send_to_0": "email_in_registry"}

        response = self.client.post(reverse("webwhois:form_personal_info"), post)

        self.assertContains(response, 'Request to send personal information')
        self.assertEqual(response.context['form'].errors, form_errors)
        self.assertEqual(PUBLIC_REQUEST.mock_calls,
                         [call.create_personal_info_request_registry_email('foo.cz', 42)])
        properties = [('handle', 'foo.cz'), ('handleType', 'contact'), ('sendTo', 'email_in_registry')]
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'PersonalInfo', properties=properties),
            call().close(properties=[('reason', exception_code)], references=[])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Fail')

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

    def _block_unblock(self, block_action, url_name, object_name, confirmation_method, lock_type,
                       action_name, object_type, signed_type, block_type, title, message):
        post = {
            "handle": "FOO",
            "object_type": object_name,
            "confirmation_method": confirmation_method,
            "lock_type": lock_type,
        }
        properties = [
            ('handle', 'FOO'),
            ('handleType', object_name),
            ('confirmMethod', confirmation_method),
        ]
        self.LOGGER.create_request.return_value.request_type = action_name
        PUBLIC_REQUEST.create_block_unblock_request.return_value = 24
        response = self.client.post(reverse(url_name), post, follow=True)
        if confirmation_method == 'signed_email':
            url_name = "webwhois:custom_email_response"
        else:
            url_name = "webwhois:notarized_letter_response"
        self.assertRedirects(response, reverse(url_name, kwargs={"public_key": self.public_key}))
        self.assertContains(response, title)
        self.assertContains(response, message)
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_block_unblock_request(object_type, 'FOO', 42, signed_type, block_type)
        ])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', action_name, properties=properties),
            call().close(properties=[], references=[('publicrequest', 24)])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')
        public_response = BlockResponse(object_name, 24, action_name, 'FOO', block_action, lock_type,
                                        confirmation_method)
        self.assertEqual(cache.get(self.public_key), public_response)

    def _block_transfer_signed_email(self, object_name, object_type, title, message):
        lock_type = "transfer"
        action_name = "BlockTransfer"
        block_type = LockRequestType.block_transfer
        confirmation_method = "signed_email"
        signed_type = ConfirmedBy.signed_email
        self._block_unblock("block", "webwhois:form_block_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def _block_all_signed_email(self, object_name, object_type, title, message):
        lock_type = "all"
        action_name = "BlockChanges"
        block_type = LockRequestType.block_transfer_and_update
        confirmation_method = "signed_email"
        signed_type = ConfirmedBy.signed_email
        self._block_unblock("block", "webwhois:form_block_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def _unblock_transfer_signed_email(self, object_name, object_type, title, message):
        lock_type = "transfer"
        action_name = "UnblockTransfer"
        block_type = LockRequestType.unblock_transfer
        confirmation_method = "signed_email"
        signed_type = ConfirmedBy.signed_email
        self._block_unblock("unblock", "webwhois:form_unblock_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def _unblock_all_signed_email(self, object_name, object_type, title, message):
        lock_type = "all"
        action_name = "UnblockChanges"
        block_type = LockRequestType.unblock_transfer_and_update
        confirmation_method = "signed_email"
        signed_type = ConfirmedBy.signed_email
        self._block_unblock("unblock", "webwhois:form_unblock_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def test_block_transfer_signed_email_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = 'Request to enable enhanced object security of domain name FOO'
        message = 'I hereby confirm the request to block any change of the sponsoring registrar for the domain name ' \
                  'FOO submitted through the web form on the web site http://testserver/whois/block-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24, and I request the activation ' \
                  'of the specified blocking option. I agree that, regarding the particular domain name FOO, ' \
                  'no change of the sponsoring registrar will be possible until I cancel the blocking option ' \
                  'through the applicable form on the company website.'
        self._block_transfer_signed_email(object_name, object_type, title, message)

    def test_block_transfer_signed_email_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = 'Request to enable enhanced object security of contact FOO'
        message = 'I hereby confirm the request to block any change of the sponsoring registrar for the contact ' \
                  'FOO submitted through the web form on the web site http://testserver/whois/block-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24, and I request the activation ' \
                  'of the specified blocking option. I agree that, regarding the particular contact FOO, ' \
                  'no change of the sponsoring registrar will be possible until I cancel the blocking option ' \
                  'through the applicable form on the company website.'
        self._block_transfer_signed_email(object_name, object_type, title, message)

    def test_block_transfer_signed_email_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = 'Request to enable enhanced object security of nameserver set FOO'
        message = 'I hereby confirm the request to block any change of the sponsoring registrar for the nameserver ' \
                  'set FOO submitted through the web form on the web site http://testserver/whois/block-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24, and I request the activation ' \
                  'of the specified blocking option. I agree that, regarding the particular nameserver set FOO, ' \
                  'no change of the sponsoring registrar will be possible until I cancel the blocking option ' \
                  'through the applicable form on the company website.'
        self._block_transfer_signed_email(object_name, object_type, title, message)

    def test_block_transfer_signed_email_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = 'Request to enable enhanced object security of keyset FOO'
        message = 'I hereby confirm the request to block any change of the sponsoring registrar for the keyset ' \
                  'FOO submitted through the web form on the web site http://testserver/whois/block-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24, and I request the activation ' \
                  'of the specified blocking option. I agree that, regarding the particular keyset FOO, ' \
                  'no change of the sponsoring registrar will be possible until I cancel the blocking option ' \
                  'through the applicable form on the company website.'
        self._block_transfer_signed_email(object_name, object_type, title, message)

    def test_unblock_transfer_signed_email_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = 'Request to disable enhanced object security of domain name FOO'
        message = 'I hereby confirm the request to cancel the blocking of the sponsoring registrar change for ' \
                  'the domain name FOO submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_transfer_signed_email(object_name, object_type, title, message)

    def test_unblock_transfer_signed_email_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = 'Request to disable enhanced object security of contact FOO'
        message = 'I hereby confirm the request to cancel the blocking of the sponsoring registrar change for ' \
                  'the contact FOO submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_transfer_signed_email(object_name, object_type, title, message)

    def test_unblock_transfer_signed_email_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = 'Request to disable enhanced object security of nameserver set FOO'
        message = 'I hereby confirm the request to cancel the blocking of the sponsoring registrar change for ' \
                  'the nameserver set FOO submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_transfer_signed_email(object_name, object_type, title, message)

    def test_unblock_transfer_signed_email_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = 'Request to disable enhanced object security of keyset FOO'
        message = 'I hereby confirm the request to cancel the blocking of the sponsoring registrar change for ' \
                  'the keyset FOO submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_transfer_signed_email(object_name, object_type, title, message)

    def test_block_all_signed_email_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = 'Request to enable enhanced object security of domain name FOO'
        message = 'I hereby confirm the request to block all changes made to domain name FOO submitted through ' \
                  'the web form on the web site http://testserver/whois/block-object/ on March 8, 2017 with ' \
                  'the assigned identification number 24, and I request the activation of the specified blocking ' \
                  'option. I agree that, with respect to the particular domain name FOO, no change will be possible ' \
                  'until I cancel the blocking option through the applicable form on the company website.'
        self._block_all_signed_email(object_name, object_type, title, message)

    def test_block_all_signed_email_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = 'Request to enable enhanced object security of contact FOO'
        message = 'I hereby confirm the request to block all changes made to contact FOO submitted through ' \
                  'the web form on the web site http://testserver/whois/block-object/ on March 8, 2017 with ' \
                  'the assigned identification number 24, and I request the activation of the specified blocking ' \
                  'option. I agree that, with respect to the particular contact FOO, no change will be possible ' \
                  'until I cancel the blocking option through the applicable form on the company website.'
        self._block_all_signed_email(object_name, object_type, title, message)

    def test_block_all_signed_email_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = 'Request to enable enhanced object security of nameserver set FOO'
        message = 'I hereby confirm the request to block all changes made to nameserver set FOO submitted through ' \
                  'the web form on the web site http://testserver/whois/block-object/ on March 8, 2017 with ' \
                  'the assigned identification number 24, and I request the activation of the specified blocking ' \
                  'option. I agree that, with respect to the particular nameserver set FOO, no change will be ' \
                  'possible until I cancel the blocking option through the applicable form on the company website.'
        self._block_all_signed_email(object_name, object_type, title, message)

    def test_block_all_signed_email_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = 'Request to enable enhanced object security of keyset FOO'
        message = 'I hereby confirm the request to block all changes made to keyset FOO submitted through ' \
                  'the web form on the web site http://testserver/whois/block-object/ on March 8, 2017 with ' \
                  'the assigned identification number 24, and I request the activation of the specified blocking ' \
                  'option. I agree that, with respect to the particular keyset FOO, no change will be ' \
                  'possible until I cancel the blocking option through the applicable form on the company website.'
        self._block_all_signed_email(object_name, object_type, title, message)

    def test_unblock_all_signed_email_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = 'Request to disable enhanced object security of domain name FOO'
        message = 'I hereby confirm the request to cancel the blocking of all changes for the domain name FOO ' \
                  'submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_all_signed_email(object_name, object_type, title, message)

    def test_unblock_all_signed_email_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = 'Request to disable enhanced object security of contact FOO'
        message = 'I hereby confirm the request to cancel the blocking of all changes for the contact FOO ' \
                  'submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_all_signed_email(object_name, object_type, title, message)

    def test_unblock_all_signed_email_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = 'Request to disable enhanced object security of nameserver set FOO'
        message = 'I hereby confirm the request to cancel the blocking of all changes for the nameserver set FOO ' \
                  'submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_all_signed_email(object_name, object_type, title, message)

    def test_unblock_all_signed_email_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = 'Request to disable enhanced object security of keyset FOO'
        message = 'I hereby confirm the request to cancel the blocking of all changes for the keyset FOO ' \
                  'submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_all_signed_email(object_name, object_type, title, message)

    def _block_transfer_notarized_letter(self, object_name, object_type, title, message):
        lock_type = "transfer"
        action_name = "BlockTransfer"
        block_type = LockRequestType.block_transfer
        confirmation_method = "notarized_letter"
        signed_type = ConfirmedBy.notarized_letter
        self._block_unblock("block", "webwhois:form_block_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def _unblock_transfer_notarized_letter(self, object_name, object_type, title, message):
        lock_type = "transfer"
        action_name = "UnblockTransfer"
        block_type = LockRequestType.unblock_transfer
        confirmation_method = "notarized_letter"
        signed_type = ConfirmedBy.notarized_letter
        self._block_unblock("unblock", "webwhois:form_unblock_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def _block_all_notarized_letter(self, object_name, object_type, title, message):
        lock_type = "all"
        action_name = "BlockChanges"
        block_type = LockRequestType.block_transfer_and_update
        confirmation_method = "notarized_letter"
        signed_type = ConfirmedBy.notarized_letter
        self._block_unblock("block", "webwhois:form_block_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def _unblock_all_notarized_letter(self, object_name, object_type, title, message):
        lock_type = "all"
        action_name = "UnblockChanges"
        block_type = LockRequestType.unblock_transfer_and_update
        confirmation_method = "notarized_letter"
        signed_type = ConfirmedBy.notarized_letter
        self._block_unblock("unblock", "webwhois:form_unblock_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def test_block_transfer_notarized_letter_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = 'Request to enable enhanced object security of domain name FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Enabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._block_transfer_notarized_letter(object_name, object_type, title, message)

    def test_block_transfer_notarized_letter_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = 'Request to enable enhanced object security of contact FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Enabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._block_transfer_notarized_letter(object_name, object_type, title, message)

    def test_block_transfer_notarized_letter_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = 'Request to enable enhanced object security of nameserver set FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Enabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._block_transfer_notarized_letter(object_name, object_type, title, message)

    def test_block_transfer_notarized_letter_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = 'Request to enable enhanced object security of keyset FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Enabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._block_transfer_notarized_letter(object_name, object_type, title, message)

    def test_unblock_transfer_notarized_letter_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = 'Request to disable enhanced object security of domain name FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Disabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._unblock_transfer_notarized_letter(object_name, object_type, title, message)

    def test_unblock_transfer_notarized_letter_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = 'Request to disable enhanced object security of contact FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Disabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._unblock_transfer_notarized_letter(object_name, object_type, title, message)

    def test_unblock_transfer_notarized_letter_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = 'Request to disable enhanced object security of nameserver set FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Disabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._unblock_transfer_notarized_letter(object_name, object_type, title, message)

    def test_unblock_transfer_notarized_letter_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = 'Request to disable enhanced object security of keyset FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Disabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._unblock_transfer_notarized_letter(object_name, object_type, title, message)

    def test_block_all_notarized_letter_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = 'Request to enable enhanced object security of domain name FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Enabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._block_all_notarized_letter(object_name, object_type, title, message)

    def test_block_all_notarized_letter_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = 'Request to enable enhanced object security of contact FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Enabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._block_all_notarized_letter(object_name, object_type, title, message)

    def test_block_all_notarized_letter_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = 'Request to enable enhanced object security of nameserver set FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Enabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._block_all_notarized_letter(object_name, object_type, title, message)

    def test_block_all_notarized_letter_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = 'Request to enable enhanced object security of keyset FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Enabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._block_all_notarized_letter(object_name, object_type, title, message)

    def test_unblock_all_notarized_letter_domain(self):
        object_name = 'domain'
        object_type = ObjectType_PR.domain
        title = 'Request to disable enhanced object security of domain name FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Disabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._unblock_all_notarized_letter(object_name, object_type, title, message)

    def test_unblock_all_notarized_letter_contact(self):
        object_name = 'contact'
        object_type = ObjectType_PR.contact
        title = 'Request to disable enhanced object security of contact FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Disabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._unblock_all_notarized_letter(object_name, object_type, title, message)

    def test_unblock_all_notarized_letter_nsset(self):
        object_name = 'nsset'
        object_type = ObjectType_PR.nsset
        title = 'Request to disable enhanced object security of nameserver set FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Disabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._unblock_all_notarized_letter(object_name, object_type, title, message)

    def test_unblock_all_notarized_letter_keyset(self):
        object_name = 'keyset'
        object_type = ObjectType_PR.keyset
        title = 'Request to disable enhanced object security of keyset FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Disabling enhanced object security ' \
                  'Request</a> (PDF)' % self.public_key
        self._unblock_all_notarized_letter(object_name, object_type, title, message)

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
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'BlockTransfer', properties=[
                ('handle', 'foo.cz'),
                ('handleType', 'domain'),
                ('confirmMethod', 'signed_email'),
            ]),
            call().close(properties=[('reason', exception_code)], references=[])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Fail')

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
        self.LOGGER = apply_patch(self, patch("webwhois.views.public_request.LOGGER"))
        apply_patch(self, patch("webwhois.views.public_request_mixin.LOGGER", self.LOGGER))
        apply_patch(self, patch("webwhois.views.logger_mixin.LOGGER", self.LOGGER))
        self.LOGGER.create_request.return_value.request_id = 21
        self.LOGGER.create_request.return_value.result = 'Error'

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
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'NotarizedLetterPdf', properties=[
                ('handle', 'FOO'),
                ('objectType', 'contact'),
                ('pdfLangCode', 'en'),
                ('documentType', 'AuthInfo')
            ]),
            call().close(properties=[], references=[('publicrequest', 42)])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')

    def test_no_data(self):
        response = self.client.get(reverse("webwhois:notarized_letter_serve_pdf",
                                           kwargs={"public_key": self.public_key}))
        self.assertIsInstance(response, HttpResponseNotFound)
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [])

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
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'NotarizedLetterPdf', properties=[
                ('handle', 'FOO'),
                ('objectType', 'contact'),
                ('pdfLangCode', 'en'),
                ('documentType', 'AuthInfo'),
                ('customEmail', 'foo@foo.off'),
            ]),
            call().close(properties=[], references=[('publicrequest', 42)])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')

    def test_download_without_logger(self):
        self.LOGGER.__bool__.return_value = False
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
        self.assertEqual(self.LOGGER.create_request.mock_calls, [])

    def test_object_not_found(self):
        cache.set(self.public_key, SendPasswordResponse('contact', 42, 'AuthInfo', 'FOO', None, None))
        PUBLIC_REQUEST.create_public_request_pdf.side_effect = OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:notarized_letter_serve_pdf",
                                           kwargs={"public_key": self.public_key}))
        self.assertIsInstance(response, HttpResponseNotFound)
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_public_request_pdf(42, Language.en)
        ])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'NotarizedLetterPdf', properties=[
                ('handle', 'FOO'),
                ('objectType', 'contact'),
                ('pdfLangCode', 'en'),
                ('documentType', 'AuthInfo')
            ]),
            call().close(properties=[('reason', 'OBJECT_NOT_FOUND')], references=[])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Fail')

    def test_unexpected_exception(self):
        cache.set(self.public_key, SendPasswordResponse('contact', 42, 'AuthInfo', 'FOO', None))
        PUBLIC_REQUEST.create_public_request_pdf.side_effect = TestException
        with self.assertRaises(TestException):
            self.client.get(reverse("webwhois:notarized_letter_serve_pdf", kwargs={"public_key": self.public_key}))
        self.assertEqual(PUBLIC_REQUEST.mock_calls, [
            call.create_public_request_pdf(42, Language.en)
        ])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'NotarizedLetterPdf', properties=[
                ('handle', 'FOO'),
                ('objectType', 'contact'),
                ('pdfLangCode', 'en'),
                ('documentType', 'AuthInfo')
            ]),
            call().close(properties=[('exception', 'TestException')], references=[])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Error')


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
                   ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestResponseErrorMessage(SimpleTestCase):

    public_key = "1234567890123456789012345678901234567890123456789012345678901234"

    def _assert_response(self, path):
        response = self.client.get(path, follow=True)
        self.assertContains(response, '<div class="error">'
                            'Sorry, but the request does not exist or has expired. Please enter a new one.'
                            '</div>', html=True)
        self.assertRedirects(response, reverse("webwhois:response_not_found", kwargs={"public_key": self.public_key}))

    def test_email_in_registry_response(self):
        self._assert_response(reverse("webwhois:email_in_registry_response", kwargs={"public_key": self.public_key}))

    def test_custom_email_response(self):
        self._assert_response(reverse("webwhois:custom_email_response", kwargs={"public_key": self.public_key}))

    def test_notarized_letter_response(self):
        self._assert_response(reverse("webwhois:notarized_letter_response", kwargs={"public_key": self.public_key}))
