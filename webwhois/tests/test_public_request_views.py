import datetime

from django.core.cache import cache
from django.http import HttpResponseNotFound
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils.html import escape
from mock import call, patch

from webwhois.tests.utils import TEMPLATES, WebwhoisAssertMixin, apply_patch
from webwhois.utils.corba_wrapper import REGISTRY_MODULE
from webwhois.views.public_request import BaseResponseTemplateView, CustomEmailView, NotarizedLetterView, \
    ResponseDataKeyMissing


@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestForms(WebwhoisAssertMixin, SimpleTestCase):

    def _assert_form_urls(self, context):
        self.assertEqual(context['form_block_object_url'], '/whois/block-object/')
        self.assertEqual(context['form_block_object_url_lock_type_all'], '/whois/block-object/?lock_type=all')
        self.assertEqual(context['form_unblock_object_url'], '/whois/unblock-object/')
        self.assertEqual(context['form_unblock_object_url_lock_type_all'], '/whois/unblock-object/?lock_type=all')

    def test_send_password(self):
        response = self.client.get(reverse("webwhois:form_send_password"))
        self.assertXpathEqual(response, "//table/caption/text()", ["Send password for transfer"])
        self.assertXpathEqual(response, "(//input[@type!='hidden']/@name|//select/@name)", [
            'object_type', 'handle', 'send_to', 'send_to', 'custom_email', 'confirmation_method'
        ])
        self._assert_form_urls(response.context)

    def test_block_object(self):
        response = self.client.get(reverse("webwhois:form_block_object"))
        self.assertXpathEqual(response, "//table/caption/text()", ["Block"])
        self.assertXpathEqual(response, "(//input[@type!='hidden']/@name|//select/@name)", [
            'lock_type', 'lock_type', 'object_type', 'handle', 'confirmation_method'
        ])
        self._assert_form_urls(response.context)

    def test_unblock_object(self):
        response = self.client.get(reverse("webwhois:form_unblock_object"))
        self.assertXpathEqual(response, "//table/caption/text()", ["Unblock"])
        self.assertXpathEqual(response, "(//input[@type!='hidden']/@name|//select/@name)", [
            'lock_type', 'lock_type', 'object_type', 'handle', 'confirmation_method'
        ])
        self._assert_form_urls(response.context)

    def test_form_param_send_to(self):
        params = "?handle=foo&object_type=nsset&send_to=custom_email"
        response = self.client.get(reverse("webwhois:form_send_password") + params)
        self.assertEqual(response.context['form'].initial, {'object_type': 'nsset', 'handle': 'foo',
                                                            'send_to': 'custom_email'})
        self.assertXpathEqual(response, "//table/caption/text()", ["Send password for transfer"])
        self.assertXpathEqual(response, "//input[@name='handle']/@value", ['foo'])
        self.assertXpathEqual(response, "//select[@name='object_type']/option[@selected='selected']/@value", ['nsset'])
        self.assertXpathEqual(response, "//input[@name='send_to'][@checked='checked']/@value", ['custom_email'])

    def test_form_param_block_unblock(self):
        params = "?handle=foo&object_type=nsset&lock_type=all"
        response = self.client.get(reverse("webwhois:form_block_object") + params)
        self.assertEqual(response.context['form'].initial, {'handle': 'foo', 'lock_type': 'all',
                                                            'object_type': 'nsset'})
        self.assertXpathEqual(response, "//table/caption/text()", ["Block"])
        self.assertXpathEqual(response, "//input[@name='handle']/@value", ['foo'])
        self.assertXpathEqual(response, "//select[@name='object_type']/option[@selected='selected']/@value", ['nsset'])
        self.assertXpathEqual(response, "//input[@name='lock_type'][@checked='checked']/@value", ['all'])


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
                   SESSION_ENGINE='django.contrib.sessions.backends.cache', ROOT_URLCONF='webwhois.tests.urls',
                   MIDDLEWARE=('django.contrib.sessions.middleware.SessionMiddleware',))
class SubmittedFormTestCase(SimpleTestCase):

    public_key = "1234567890123456789012345678901234567890123456789012345678901234"

    def setUp(self):
        self.PUBLIC_REQUEST = apply_patch(self, patch("webwhois.views.public_request.PUBLIC_REQUEST"))
        self.LOGGER = apply_patch(self, patch("webwhois.views.logger_mixin.LOGGER"))
        self.LOGGER.create_request.return_value.request_id = 42
        self.LOGGER.create_request.return_value.result = 'Error'
        self.LOGGER.create_request.return_value.request_type = 'AuthInfo'
        apply_patch(self, patch("webwhois.views.public_request_mixin.LOGGER", self.LOGGER))
        mock_timezone_now = apply_patch(self, patch("webwhois.views.public_request_mixin.timezone_now"))
        mock_timezone_now.return_value.date.return_value = datetime.date(2017, 3, 8)
        apply_patch(self, patch("webwhois.views.public_request_mixin.get_random_string", lambda n: self.public_key))

    def tearDown(self):
        cache.clear()


@override_settings(TEMPLATES=TEMPLATES)
class TestSendPasswodForm(SubmittedFormTestCase):

    def _send_password_email_in_registry(self, post, action_name, properties, object_type, title, message):
        self.PUBLIC_REQUEST.create_authinfo_request_registry_email.return_value = 24
        response = self.client.post(reverse("webwhois:form_send_password"), post, follow=True)
        path = reverse("webwhois:email_in_registry_response", kwargs={"public_key": self.public_key})
        self.assertRedirects(response, path)
        self.assertContains(response, title)
        self.assertContains(response, message)
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [
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
            "send_to": "email_in_registry",
        }
        properties = [
            ('handle', 'foo.cz'),
            ('handleType', 'domain'),
            ('confirmMethod', 'signed_email'),
            ('sendTo', 'email_in_registry'),
        ]
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        title = "Request for password for transfer domain name foo.cz"
        message = "We received successfully your request for a password to change the domain <strong>foo.cz</strong> " \
                  "sponsoring registrar. An email with the password will be sent to the email address of domain " \
                  "holder and admin contacts."
        self._send_password_email_in_registry(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_email_in_registry_contact(self):
        post = {
            "object_type": "contact",
            "handle": "CONTACT",
            "confirmation_method": "signed_email",
            "send_to": "email_in_registry",
        }
        properties = [
            ('handle', 'CONTACT'),
            ('handleType', 'contact'),
            ('confirmMethod', 'signed_email'),
            ('sendTo', 'email_in_registry'),
        ]
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.contact
        title = "Request for password for transfer contact CONTACT"
        message = "We received successfully your request for a password to change the contact " \
                  "<strong>CONTACT</strong> sponsoring registrar. An email with the password will be sent to " \
                  "the email address from the registry."
        self._send_password_email_in_registry(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_email_in_registry_nsset(self):
        post = {
            "object_type": "nsset",
            "handle": "NSSET",
            "confirmation_method": "signed_email",
            "send_to": "email_in_registry",
        }
        properties = [
            ('handle', 'NSSET'),
            ('handleType', 'nsset'),
            ('confirmMethod', 'signed_email'),
            ('sendTo', 'email_in_registry'),
        ]
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.nsset
        title = "Request for password for transfer nameserver set NSSET"
        message = "We received successfully your request for a password to change the nameserver set " \
                  "<strong>NSSET</strong> sponsoring registrar. An email with the password will be sent to the email " \
                  "addresses of the nameserver set's technical contacts."
        self._send_password_email_in_registry(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_email_in_registry_keyset(self):
        post = {
            "object_type": "keyset",
            "handle": "KEYSET",
            "confirmation_method": "signed_email",
            "send_to": "email_in_registry",
        }
        properties = [
            ('handle', 'KEYSET'),
            ('handleType', 'keyset'),
            ('confirmMethod', 'signed_email'),
            ('sendTo', 'email_in_registry'),
        ]
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.keyset
        title = "Request for password for transfer keyset KEYSET"
        message = "We received successfully your request for a password to change the keyset " \
                  "<strong>KEYSET</strong> sponsoring registrar. An email with the password will be sent to " \
                  "the email addresses of the keyset's technical contacts."
        self._send_password_email_in_registry(post, 'AuthInfo', properties, object_type, title, message)

    def _assert_send_password_exception(self, exception_code, form_error_message):
        post = {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to": "email_in_registry",
        }
        response = self.client.post(reverse("webwhois:form_send_password"), post)
        self.assertEqual(response.context['form'].errors, {'handle': [form_error_message]})
        self.assertContains(response, form_error_message)
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [
            call.create_authinfo_request_registry_email(object_type, 'foo.cz', 42)
        ])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'AuthInfo', properties=[
                ('handle', 'foo.cz'),
                ('handleType', 'domain'),
                ('confirmMethod', 'signed_email'),
                ('sendTo', 'email_in_registry')
            ]),
            call().close(properties=[('reason', exception_code)], references=[])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Fail')

    def test_send_password_object_not_found(self):
        self.PUBLIC_REQUEST.create_authinfo_request_registry_email.side_effect = REGISTRY_MODULE.PublicRequest. \
                                                                                 OBJECT_NOT_FOUND
        self._assert_send_password_exception('OBJECT_NOT_FOUND', 'Object not found. Check that you have correctly '
                                             'entered the Object type and Handle.')

    def test_send_password_object_transfer_prohibited(self):
        self.PUBLIC_REQUEST.create_authinfo_request_registry_email.side_effect = REGISTRY_MODULE.PublicRequest. \
                                                                                 OBJECT_TRANSFER_PROHIBITED
        self._assert_send_password_exception('OBJECT_TRANSFER_PROHIBITED', 'Transfer of object is prohibited. '
                                             'The request can not be accepted.')

    def test_send_password_invalid_email(self):
        self.PUBLIC_REQUEST.create_authinfo_request_non_registry_email.side_effect = REGISTRY_MODULE.PublicRequest. \
                                                                                     INVALID_EMAIL
        post = {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to": "custom_email",
            "custom_email": "foo@foo.off",
        }
        response = self.client.post(reverse("webwhois:form_send_password"), post)
        self.assertEqual(response.context['form'].errors, {
            'custom_email': ['The email was not found or the address is not valid.']
        })
        self.assertContains(response, 'The email was not found or the address is not valid.')
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        signed_email = REGISTRY_MODULE.PublicRequest.ConfirmedBy.signed_email
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [
            call.create_authinfo_request_non_registry_email(object_type, 'foo.cz', 42, signed_email, 'foo@foo.off')
        ])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'AuthInfo', properties=[
                ('handle', 'foo.cz'),
                ('handleType', 'domain'),
                ('confirmMethod', 'signed_email'),
                ('sendTo', 'custom_email'),
                ('customEmail', 'foo@foo.off')]),
            call().close(properties=[('reason', 'INVALID_EMAIL')], references=[])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Fail')

    def _send_password_confirm_method(self, confirm_method, post, action_name, properties, object_type, title, message):
        self.PUBLIC_REQUEST.create_authinfo_request_non_registry_email.return_value = 24
        response = self.client.post(reverse("webwhois:form_send_password"), post, follow=True)
        if post['confirmation_method'] == 'signed_email':
            url_name = "webwhois:custom_email_response"
        else:
            url_name = "webwhois:notarized_letter_response"
        self.assertRedirects(response, reverse(url_name, kwargs={"public_key": self.public_key}))
        self.assertContains(response, title)
        self.assertContains(response, message)
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [
            call.create_authinfo_request_non_registry_email(object_type, post['handle'], 42, confirm_method,
                                                            'foo@foo.off')
        ])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'AuthInfo', properties=properties),
            call().close(properties=[], references=[('publicrequest', 24)])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')

    def _send_password_to_custom_email(self, post, action_name, properties, object_type, title, message):
        conftype = REGISTRY_MODULE.PublicRequest.ConfirmedBy.signed_email
        self._send_password_confirm_method(conftype, post, action_name, properties, object_type, title, message)

    def _send_password_notarized_letter(self, post, action_name, properties, object_type, title, message):
        conftype = REGISTRY_MODULE.PublicRequest.ConfirmedBy.notarized_letter
        self._send_password_confirm_method(conftype, post, action_name, properties, object_type, title, message)

    def test_send_password_custom_email_domain(self):
        post = {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to": "custom_email",
            "custom_email": "foo@foo.off",
        }
        properties = [
            ('handle', 'foo.cz'),
            ('handleType', 'domain'),
            ('confirmMethod', 'signed_email'),
            ('sendTo', 'custom_email'),
            ('customEmail', 'foo@foo.off'),
        ]
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        title = "Request for password for transfer domain name foo.cz"
        message = "I hereby confirm my request to get the password for domain name foo.cz, submitted through " \
                  "the web form at http://testserver/whois/send-password/ on March 8, 2017, assigned id number 24. " \
                  "Please send the password to foo@foo.off."
        self._send_password_to_custom_email(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_custom_email_contact(self):
        post = {
            "object_type": "contact",
            "handle": "FOO",
            "confirmation_method": "signed_email",
            "send_to": "custom_email",
            "custom_email": "foo@foo.off",
        }
        properties = [
            ('handle', 'FOO'),
            ('handleType', 'contact'),
            ('confirmMethod', 'signed_email'),
            ('sendTo', 'custom_email'),
            ('customEmail', 'foo@foo.off'),
        ]
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.contact
        title = "Request for password for transfer contact FOO"
        message = "I hereby confirm my request to get the password for contact FOO, submitted through " \
                  "the web form at http://testserver/whois/send-password/ on March 8, 2017, assigned id number 24. " \
                  "Please send the password to foo@foo.off."
        self._send_password_to_custom_email(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_custom_email_nsset(self):
        post = {
            "object_type": "nsset",
            "handle": "FOO",
            "confirmation_method": "signed_email",
            "send_to": "custom_email",
            "custom_email": "foo@foo.off",
        }
        properties = [
            ('handle', 'FOO'),
            ('handleType', 'nsset'),
            ('confirmMethod', 'signed_email'),
            ('sendTo', 'custom_email'),
            ('customEmail', 'foo@foo.off'),
        ]
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.nsset
        title = "Request for password for transfer nameserver set FOO"
        message = "I hereby confirm my request to get the password for nameserver set FOO, submitted through " \
                  "the web form at http://testserver/whois/send-password/ on March 8, 2017, assigned id number 24. " \
                  "Please send the password to foo@foo.off."
        self._send_password_to_custom_email(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_custom_email_keyset(self):
        post = {
            "object_type": "keyset",
            "handle": "FOO",
            "confirmation_method": "signed_email",
            "send_to": "custom_email",
            "custom_email": "foo@foo.off",
        }
        properties = [
            ('handle', 'FOO'),
            ('handleType', 'keyset'),
            ('confirmMethod', 'signed_email'),
            ('sendTo', 'custom_email'),
            ('customEmail', 'foo@foo.off'),
        ]
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.keyset
        title = "Request for password for transfer keyset FOO"
        message = "I hereby confirm my request to get the password for keyset FOO, submitted through " \
                  "the web form at http://testserver/whois/send-password/ on March 8, 2017, assigned id number 24. " \
                  "Please send the password to foo@foo.off."
        self._send_password_to_custom_email(post, 'AuthInfo', properties, object_type, title, message)

    def test_send_password_email_in_registry_notarized_letter(self):
        post = {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "notarized_letter",
            "send_to": "email_in_registry",
        }
        response = self.client.post(reverse("webwhois:form_send_password"), post)
        self.assertEqual(response.context['form'].errors, {'__all__': [
            'Letter with officially verified signature can be sent only to the custom email. '
            'Please select "Send to custom email" and enter it.'
        ]})
        self.assertContains(response, escape(
                            'Letter with officially verified signature can be sent only to the custom email. '
                            'Please select "Send to custom email" and enter it.'))
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [])

    def _send_password_notarized_letter_registry(self, object_name, object_type, title):
        post = {
            "object_type": object_name,
            "handle": "FOO",
            "confirmation_method": "notarized_letter",
            "send_to": "custom_email",
            "custom_email": "foo@foo.off",
        }
        properties = [
            ('handle', 'FOO'),
            ('handleType', object_name),
            ('confirmMethod', 'notarized_letter'),
            ('sendTo', 'custom_email'),
            ('customEmail', 'foo@foo.off'),
        ]
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Transfer password request</a> ' \
                  '(PDF)' % self.public_key
        self._send_password_notarized_letter(post, 'AuthInfo', properties, object_type, title, message)
        self.assertEqual(cache.get(self.public_key), {
            'response_id': 24,
            'object_type': object_name,
            'handle': 'FOO',
            'custom_email': 'foo@foo.off',
            'request_name': 'AuthInfo',
            'confirmation_method': 'notarized_letter',
            'send_to': 'custom_email',
            'created_date': datetime.datetime(2017, 3, 8).date(),
        })

    def test_send_password_notarized_letter_domain(self):
        title = "Request for password for transfer domain name FOO"
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        self._send_password_notarized_letter_registry('domain', object_type, title)

    def test_send_password_notarized_letter_contact(self):
        title = "Request for password for transfer contact FOO"
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.contact
        self._send_password_notarized_letter_registry('contact', object_type, title)

    def test_send_password_notarized_letter_nsset(self):
        title = "Request for password for transfer nameserver set FOO"
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.nsset
        self._send_password_notarized_letter_registry('nsset', object_type, title)

    def test_send_password_notarized_letter_keyset(self):
        title = "Request for password for transfer keyset FOO"
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.keyset
        self._send_password_notarized_letter_registry('keyset', object_type, title)


@override_settings(TEMPLATES=TEMPLATES)
class TestBlockUnblockForm(SubmittedFormTestCase):

    def _block_unblock(self, block_unblock_action_type, url_name, object_name, confirmation_method, lock_type,
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
        self.PUBLIC_REQUEST.create_block_unblock_request.return_value = 24
        response = self.client.post(reverse(url_name), post, follow=True)
        if confirmation_method == 'signed_email':
            url_name = "webwhois:custom_email_response"
        else:
            url_name = "webwhois:notarized_letter_response"
        self.assertRedirects(response, reverse(url_name, kwargs={"public_key": self.public_key}))
        self.assertContains(response, title)
        self.assertContains(response, message)
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [
            call.create_block_unblock_request(object_type, 'FOO', 42, signed_type, block_type)
        ])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', action_name, properties=properties),
            call().close(properties=[], references=[('publicrequest', 24)])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')
        self.assertEqual(cache.get(self.public_key), {
            'response_id': 24,
            'handle': 'FOO',
            'object_type': object_name,
            'request_name': action_name,
            'lock_type': lock_type,
            'block_unblock_action_type': block_unblock_action_type,
            'confirmation_method': confirmation_method,
            'created_date': datetime.datetime(2017, 3, 8).date(),
        })

    def _block_transfer_signed_email(self, object_name, object_type, title, message):
        lock_type = "transfer"
        action_name = "BlockTransfer"
        block_type = REGISTRY_MODULE.PublicRequest.LockRequestType.block_transfer
        confirmation_method = "signed_email"
        signed_type = REGISTRY_MODULE.PublicRequest.ConfirmedBy.signed_email
        self._block_unblock("block", "webwhois:form_block_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def _block_all_signed_email(self, object_name, object_type, title, message):
        lock_type = "all"
        action_name = "BlockChanges"
        block_type = REGISTRY_MODULE.PublicRequest.LockRequestType.block_transfer_and_update
        confirmation_method = "signed_email"
        signed_type = REGISTRY_MODULE.PublicRequest.ConfirmedBy.signed_email
        self._block_unblock("block", "webwhois:form_block_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def _unblock_transfer_signed_email(self, object_name, object_type, title, message):
        lock_type = "transfer"
        action_name = "UnblockTransfer"
        block_type = REGISTRY_MODULE.PublicRequest.LockRequestType.unblock_transfer
        confirmation_method = "signed_email"
        signed_type = REGISTRY_MODULE.PublicRequest.ConfirmedBy.signed_email
        self._block_unblock("unblock", "webwhois:form_unblock_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def _unblock_all_signed_email(self, object_name, object_type, title, message):
        lock_type = "all"
        action_name = "UnblockChanges"
        block_type = REGISTRY_MODULE.PublicRequest.LockRequestType.unblock_transfer_and_update
        confirmation_method = "signed_email"
        signed_type = REGISTRY_MODULE.PublicRequest.ConfirmedBy.signed_email
        self._block_unblock("unblock", "webwhois:form_unblock_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def test_block_transfer_signed_email_domain(self):
        object_name = 'domain'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        title = 'Request for blocking of domain name FOO'
        message = 'I hereby confirm the request to block any change of the sponsoring registrar for the domain name ' \
                  'FOO submitted through the web form on the web site http://testserver/whois/block-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24, and I request the activation ' \
                  'of the specified blocking option. I agree that, regarding the particular domain name FOO, ' \
                  'no change of the sponsoring registrar will be possible until I cancel the blocking option ' \
                  'through the applicable form on the company website.'
        self._block_transfer_signed_email(object_name, object_type, title, message)

    def test_block_transfer_signed_email_contact(self):
        object_name = 'contact'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.contact
        title = 'Request for blocking of contact FOO'
        message = 'I hereby confirm the request to block any change of the sponsoring registrar for the contact ' \
                  'FOO submitted through the web form on the web site http://testserver/whois/block-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24, and I request the activation ' \
                  'of the specified blocking option. I agree that, regarding the particular contact FOO, ' \
                  'no change of the sponsoring registrar will be possible until I cancel the blocking option ' \
                  'through the applicable form on the company website.'
        self._block_transfer_signed_email(object_name, object_type, title, message)

    def test_block_transfer_signed_email_nsset(self):
        object_name = 'nsset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.nsset
        title = 'Request for blocking of nameserver set FOO'
        message = 'I hereby confirm the request to block any change of the sponsoring registrar for the nameserver ' \
                  'set FOO submitted through the web form on the web site http://testserver/whois/block-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24, and I request the activation ' \
                  'of the specified blocking option. I agree that, regarding the particular nameserver set FOO, ' \
                  'no change of the sponsoring registrar will be possible until I cancel the blocking option ' \
                  'through the applicable form on the company website.'
        self._block_transfer_signed_email(object_name, object_type, title, message)

    def test_block_transfer_signed_email_keyset(self):
        object_name = 'keyset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.keyset
        title = 'Request for blocking of keyset FOO'
        message = 'I hereby confirm the request to block any change of the sponsoring registrar for the keyset ' \
                  'FOO submitted through the web form on the web site http://testserver/whois/block-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24, and I request the activation ' \
                  'of the specified blocking option. I agree that, regarding the particular keyset FOO, ' \
                  'no change of the sponsoring registrar will be possible until I cancel the blocking option ' \
                  'through the applicable form on the company website.'
        self._block_transfer_signed_email(object_name, object_type, title, message)

    def test_unblock_transfer_signed_email_domain(self):
        object_name = 'domain'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        title = 'Request to cancel the blocking of domain name FOO'
        message = 'I hereby confirm the request to cancel the blocking of the sponsoring registrar change for ' \
                  'the domain name FOO submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_transfer_signed_email(object_name, object_type, title, message)

    def test_unblock_transfer_signed_email_contact(self):
        object_name = 'contact'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.contact
        title = 'Request to cancel the blocking of contact FOO'
        message = 'I hereby confirm the request to cancel the blocking of the sponsoring registrar change for ' \
                  'the contact FOO submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_transfer_signed_email(object_name, object_type, title, message)

    def test_unblock_transfer_signed_email_nsset(self):
        object_name = 'nsset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.nsset
        title = 'Request to cancel the blocking of nameserver set FOO'
        message = 'I hereby confirm the request to cancel the blocking of the sponsoring registrar change for ' \
                  'the nameserver set FOO submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_transfer_signed_email(object_name, object_type, title, message)

    def test_unblock_transfer_signed_email_keyset(self):
        object_name = 'keyset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.keyset
        title = 'Request to cancel the blocking of keyset FOO'
        message = 'I hereby confirm the request to cancel the blocking of the sponsoring registrar change for ' \
                  'the keyset FOO submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_transfer_signed_email(object_name, object_type, title, message)

    def test_block_all_signed_email_domain(self):
        object_name = 'domain'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        title = 'Request for blocking of domain name FOO'
        message = 'I hereby confirm the request to block all changes made to domain name FOO submitted through ' \
                  'the web form on the web site http://testserver/whois/block-object/ on March 8, 2017 with ' \
                  'the assigned identification number 24, and I request the activation of the specified blocking ' \
                  'option. I agree that, with respect to the particular domain name FOO, no change will be possible ' \
                  'until I cancel the blocking option through the applicable form on the company website.'
        self._block_all_signed_email(object_name, object_type, title, message)

    def test_block_all_signed_email_contact(self):
        object_name = 'contact'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.contact
        title = 'Request for blocking of contact FOO'
        message = 'I hereby confirm the request to block all changes made to contact FOO submitted through ' \
                  'the web form on the web site http://testserver/whois/block-object/ on March 8, 2017 with ' \
                  'the assigned identification number 24, and I request the activation of the specified blocking ' \
                  'option. I agree that, with respect to the particular contact FOO, no change will be possible ' \
                  'until I cancel the blocking option through the applicable form on the company website.'
        self._block_all_signed_email(object_name, object_type, title, message)

    def test_block_all_signed_email_nsset(self):
        object_name = 'nsset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.nsset
        title = 'Request for blocking of nameserver set FOO'
        message = 'I hereby confirm the request to block all changes made to nameserver set FOO submitted through ' \
                  'the web form on the web site http://testserver/whois/block-object/ on March 8, 2017 with ' \
                  'the assigned identification number 24, and I request the activation of the specified blocking ' \
                  'option. I agree that, with respect to the particular nameserver set FOO, no change will be ' \
                  'possible until I cancel the blocking option through the applicable form on the company website.'
        self._block_all_signed_email(object_name, object_type, title, message)

    def test_block_all_signed_email_keyset(self):
        object_name = 'keyset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.keyset
        title = 'Request for blocking of keyset FOO'
        message = 'I hereby confirm the request to block all changes made to keyset FOO submitted through ' \
                  'the web form on the web site http://testserver/whois/block-object/ on March 8, 2017 with ' \
                  'the assigned identification number 24, and I request the activation of the specified blocking ' \
                  'option. I agree that, with respect to the particular keyset FOO, no change will be ' \
                  'possible until I cancel the blocking option through the applicable form on the company website.'
        self._block_all_signed_email(object_name, object_type, title, message)

    def test_unblock_all_signed_email_domain(self):
        object_name = 'domain'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        title = 'Request to cancel the blocking of domain name FOO'
        message = 'I hereby confirm the request to cancel the blocking of all changes for the domain name FOO ' \
                  'submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_all_signed_email(object_name, object_type, title, message)

    def test_unblock_all_signed_email_contact(self):
        object_name = 'contact'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.contact
        title = 'Request to cancel the blocking of contact FOO'
        message = 'I hereby confirm the request to cancel the blocking of all changes for the contact FOO ' \
                  'submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_all_signed_email(object_name, object_type, title, message)

    def test_unblock_all_signed_email_nsset(self):
        object_name = 'nsset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.nsset
        title = 'Request to cancel the blocking of nameserver set FOO'
        message = 'I hereby confirm the request to cancel the blocking of all changes for the nameserver set FOO ' \
                  'submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_all_signed_email(object_name, object_type, title, message)

    def test_unblock_all_signed_email_keyset(self):
        object_name = 'keyset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.keyset
        title = 'Request to cancel the blocking of keyset FOO'
        message = 'I hereby confirm the request to cancel the blocking of all changes for the keyset FOO ' \
                  'submitted through the web form on http://testserver/whois/unblock-object/ ' \
                  'on March 8, 2017 with the assigned identification number 24.'
        self._unblock_all_signed_email(object_name, object_type, title, message)

    def _block_transfer_notarized_letter(self, object_name, object_type, title, message):
        lock_type = "transfer"
        action_name = "BlockTransfer"
        block_type = REGISTRY_MODULE.PublicRequest.LockRequestType.block_transfer
        confirmation_method = "notarized_letter"
        signed_type = REGISTRY_MODULE.PublicRequest.ConfirmedBy.notarized_letter
        self._block_unblock("block", "webwhois:form_block_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def _unblock_transfer_notarized_letter(self, object_name, object_type, title, message):
        lock_type = "transfer"
        action_name = "UnblockTransfer"
        block_type = REGISTRY_MODULE.PublicRequest.LockRequestType.unblock_transfer
        confirmation_method = "notarized_letter"
        signed_type = REGISTRY_MODULE.PublicRequest.ConfirmedBy.notarized_letter
        self._block_unblock("unblock", "webwhois:form_unblock_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def _block_all_notarized_letter(self, object_name, object_type, title, message):
        lock_type = "all"
        action_name = "BlockChanges"
        block_type = REGISTRY_MODULE.PublicRequest.LockRequestType.block_transfer_and_update
        confirmation_method = "notarized_letter"
        signed_type = REGISTRY_MODULE.PublicRequest.ConfirmedBy.notarized_letter
        self._block_unblock("block", "webwhois:form_block_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def _unblock_all_notarized_letter(self, object_name, object_type, title, message):
        lock_type = "all"
        action_name = "UnblockChanges"
        block_type = REGISTRY_MODULE.PublicRequest.LockRequestType.unblock_transfer_and_update
        confirmation_method = "notarized_letter"
        signed_type = REGISTRY_MODULE.PublicRequest.ConfirmedBy.notarized_letter
        self._block_unblock("unblock", "webwhois:form_unblock_object", object_name, confirmation_method, lock_type,
                            action_name, object_type, signed_type, block_type, title, message)

    def test_block_transfer_notarized_letter_domain(self):
        object_name = 'domain'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        title = 'Request for blocking of domain name FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Blocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._block_transfer_notarized_letter(object_name, object_type, title, message)

    def test_block_transfer_notarized_letter_contact(self):
        object_name = 'contact'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.contact
        title = 'Request for blocking of contact FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Blocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._block_transfer_notarized_letter(object_name, object_type, title, message)

    def test_block_transfer_notarized_letter_nsset(self):
        object_name = 'nsset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.nsset
        title = 'Request for blocking of nameserver set FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Blocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._block_transfer_notarized_letter(object_name, object_type, title, message)

    def test_block_transfer_notarized_letter_keyset(self):
        object_name = 'keyset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.keyset
        title = 'Request for blocking of keyset FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Blocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._block_transfer_notarized_letter(object_name, object_type, title, message)

    def test_unblock_transfer_notarized_letter_domain(self):
        object_name = 'domain'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        title = 'Request to cancel the blocking of domain name FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Unblocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._unblock_transfer_notarized_letter(object_name, object_type, title, message)

    def test_unblock_transfer_notarized_letter_contact(self):
        object_name = 'contact'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.contact
        title = 'Request to cancel the blocking of contact FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Unblocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._unblock_transfer_notarized_letter(object_name, object_type, title, message)

    def test_unblock_transfer_notarized_letter_nsset(self):
        object_name = 'nsset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.nsset
        title = 'Request to cancel the blocking of nameserver set FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Unblocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._unblock_transfer_notarized_letter(object_name, object_type, title, message)

    def test_unblock_transfer_notarized_letter_keyset(self):
        object_name = 'keyset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.keyset
        title = 'Request to cancel the blocking of keyset FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Unblocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._unblock_transfer_notarized_letter(object_name, object_type, title, message)

    def test_block_all_notarized_letter_domain(self):
        object_name = 'domain'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        title = 'Request for blocking of domain name FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Blocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._block_all_notarized_letter(object_name, object_type, title, message)

    def test_block_all_notarized_letter_contact(self):
        object_name = 'contact'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.contact
        title = 'Request for blocking of contact FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Blocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._block_all_notarized_letter(object_name, object_type, title, message)

    def test_block_all_notarized_letter_nsset(self):
        object_name = 'nsset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.nsset
        title = 'Request for blocking of nameserver set FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Blocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._block_all_notarized_letter(object_name, object_type, title, message)

    def test_block_all_notarized_letter_keyset(self):
        object_name = 'keyset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.keyset
        title = 'Request for blocking of keyset FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Blocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._block_all_notarized_letter(object_name, object_type, title, message)

    def test_unblock_all_notarized_letter_domain(self):
        object_name = 'domain'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        title = 'Request to cancel the blocking of domain name FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Unblocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._unblock_all_notarized_letter(object_name, object_type, title, message)

    def test_unblock_all_notarized_letter_contact(self):
        object_name = 'contact'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.contact
        title = 'Request to cancel the blocking of contact FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Unblocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._unblock_all_notarized_letter(object_name, object_type, title, message)

    def test_unblock_all_notarized_letter_nsset(self):
        object_name = 'nsset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.nsset
        title = 'Request to cancel the blocking of nameserver set FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Unblocking Request</a> ' \
                  '(PDF)' % self.public_key
        self._unblock_all_notarized_letter(object_name, object_type, title, message)

    def test_unblock_all_notarized_letter_keyset(self):
        object_name = 'keyset'
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.keyset
        title = 'Request to cancel the blocking of keyset FOO'
        message = 'Please print this <a href="/whois/pdf-notarized-letter/%s/">Unblocking Request</a> ' \
                  '(PDF)' % self.public_key
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
        object_type = REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain
        signed_email = REGISTRY_MODULE.PublicRequest.ConfirmedBy.signed_email
        block_transfer = REGISTRY_MODULE.PublicRequest.LockRequestType.block_transfer
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [
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
        self.PUBLIC_REQUEST.create_block_unblock_request.side_effect = REGISTRY_MODULE.PublicRequest.OBJECT_NOT_FOUND
        self._assert_create_block_unblock_exception('OBJECT_NOT_FOUND', 'Object not found. Check that you have'
                                                    ' correctly entered the Object type and Handle.')

    def test_block_object_already_blocked(self):
        self.PUBLIC_REQUEST.create_block_unblock_request.side_effect = REGISTRY_MODULE.PublicRequest. \
                                                                       OBJECT_ALREADY_BLOCKED
        self._assert_create_block_unblock_exception('OBJECT_ALREADY_BLOCKED', 'This object is already blocked. '
                                                    'The request can not be accepted.')

    def test_unblock_object_not_blocked(self):
        self.PUBLIC_REQUEST.create_block_unblock_request.side_effect = REGISTRY_MODULE.PublicRequest. \
                                                                       OBJECT_NOT_BLOCKED
        self._assert_create_block_unblock_exception('OBJECT_NOT_BLOCKED', 'This object is not blocked. '
                                                    'The request can not be accepted.')

    def test_block_object_has_different_block(self):
        self.PUBLIC_REQUEST.create_block_unblock_request.side_effect = REGISTRY_MODULE.PublicRequest. \
                                                                       HAS_DIFFERENT_BLOCK
        self._assert_create_block_unblock_exception('HAS_DIFFERENT_BLOCK', 'This object has another active blocking. '
                                                    'The request can not be accepted.')

    def test_block_object_operation_prohibited(self):
        self.PUBLIC_REQUEST.create_block_unblock_request.side_effect = REGISTRY_MODULE.PublicRequest. \
                                                                       OPERATION_PROHIBITED
        self._assert_create_block_unblock_exception('OPERATION_PROHIBITED', 'Operation for this object is prohibited. '
                                                    'The request can not be accepted.')


class TestException(Exception):
    "Test exception"


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
                   ROOT_URLCONF='webwhois.tests.urls')
class TestNotarizedLetterPdf(SimpleTestCase):

    public_key = "1234567890123456789012345678901234567890123456789012345678901234"

    def setUp(self):
        self.PUBLIC_REQUEST = apply_patch(self, patch("webwhois.views.public_request.PUBLIC_REQUEST"))
        self.LOGGER = apply_patch(self, patch("webwhois.views.public_request.LOGGER"))
        apply_patch(self, patch("webwhois.views.public_request_mixin.LOGGER", self.LOGGER))
        apply_patch(self, patch("webwhois.views.logger_mixin.LOGGER", self.LOGGER))
        self.LOGGER.create_request.return_value.request_id = 21
        self.LOGGER.create_request.return_value.result = 'Error'

    def tearDown(self):
        cache.clear()

    def test_download(self):
        response_data = {
            'response_id': 42,
            'request_name': 'AuthInfo',
            'handle': 'FOO',
            'object_type': 'contact',
        }
        cache.set(self.public_key, response_data)
        self.PUBLIC_REQUEST.create_public_request_pdf.return_value = "PDF content..."
        response = self.client.get(reverse("webwhois:notarized_letter_serve_pdf",
                                           kwargs={"public_key": self.public_key}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'], 'attachment; filename="notarized-letter-en.pdf"')
        self.assertEqual(response.content, "PDF content...")
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [
            call.create_public_request_pdf(42, REGISTRY_MODULE.PublicRequest.Language.en)
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
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [])

    def test_no_response_id(self):
        response_data = {
            'request_name': 'AuthInfo',
            'handle': 'FOO',
            'object_type': 'contact',
        }
        cache.set(self.public_key, response_data)
        response = self.client.get(reverse("webwhois:notarized_letter_serve_pdf",
                                           kwargs={"public_key": self.public_key}))
        self.assertIsInstance(response, HttpResponseNotFound)
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [])

    @override_settings(LANGUAGE_CODE='en')
    def test_missing_values(self):
        response_data = {
            'response_id': 42
        }
        cache.set(self.public_key, response_data)
        self.PUBLIC_REQUEST.create_public_request_pdf.return_value = "PDF content..."
        response = self.client.get(reverse("webwhois:notarized_letter_serve_pdf",
                                           kwargs={"public_key": self.public_key}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'], 'attachment; filename="notarized-letter-en.pdf"')
        self.assertEqual(response.content, "PDF content...")
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [
            call.create_public_request_pdf(42, REGISTRY_MODULE.PublicRequest.Language.en)
        ])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'NotarizedLetterPdf', properties=[
                ('handle', 'missing'),
                ('objectType', 'missing'),
                ('pdfLangCode', 'en'),
                ('documentType', 'missing')
            ]),
            call().close(properties=[], references=[('publicrequest', 42)])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')

    def test_download_custom_email(self):
        response_data = {
            'response_id': 42,
            'request_name': 'AuthInfo',
            'handle': 'FOO',
            'object_type': 'contact',
            'custom_email': 'foo@foo.off'
        }
        cache.set(self.public_key, response_data)
        self.PUBLIC_REQUEST.create_public_request_pdf.return_value = "PDF content..."
        response = self.client.get(reverse("webwhois:notarized_letter_serve_pdf",
                                           kwargs={"public_key": self.public_key}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'], 'attachment; filename="notarized-letter-en.pdf"')
        self.assertEqual(response.content, "PDF content...")
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [
            call.create_public_request_pdf(42, REGISTRY_MODULE.PublicRequest.Language.en)
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
        self.LOGGER.__nonzero__.return_value = False
        response_data = {
            'response_id': 42,
            'request_name': 'AuthInfo',
            'handle': 'FOO',
            'object_type': 'contact',
        }
        cache.set(self.public_key, response_data)
        self.PUBLIC_REQUEST.create_public_request_pdf.return_value = "PDF content..."
        response = self.client.get(reverse("webwhois:notarized_letter_serve_pdf",
                                           kwargs={"public_key": self.public_key}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'], 'attachment; filename="notarized-letter-en.pdf"')
        self.assertEqual(response.content, "PDF content...")
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [
            call.create_public_request_pdf(42, REGISTRY_MODULE.PublicRequest.Language.en)
        ])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [])

    def test_object_not_found(self):
        response_data = {
            'response_id': 42,
            'request_name': 'AuthInfo',
            'handle': 'FOO',
            'object_type': 'contact',
        }
        cache.set(self.public_key, response_data)
        self.PUBLIC_REQUEST.create_public_request_pdf.side_effect = REGISTRY_MODULE.PublicRequest.OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:notarized_letter_serve_pdf",
                                           kwargs={"public_key": self.public_key}))
        self.assertIsInstance(response, HttpResponseNotFound)
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [
            call.create_public_request_pdf(42, REGISTRY_MODULE.PublicRequest.Language.en)
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
        response_data = {
            'response_id': 42,
            'request_name': 'AuthInfo',
            'handle': 'FOO',
            'object_type': 'contact',
        }
        cache.set(self.public_key, response_data)
        self.PUBLIC_REQUEST.create_public_request_pdf.side_effect = TestException
        with self.assertRaises(TestException):
            self.client.get(reverse("webwhois:notarized_letter_serve_pdf", kwargs={"public_key": self.public_key}))
        self.assertEqual(self.PUBLIC_REQUEST.mock_calls, [
            call.create_public_request_pdf(42, REGISTRY_MODULE.PublicRequest.Language.en)
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


class TestCheckResponseData(SimpleTestCase):

    response_data = {'handle': 'foo', 'response_id': 1, 'object_type': 'contact', 'created_date': '2017-04-24'}

    def _assert_response_data(self, view):
        with self.assertRaisesMessage(ResponseDataKeyMissing, 'response_data'):
            view.check_response_data({})
        with self.assertRaisesMessage(ResponseDataKeyMissing, 'object_type, response_id, created_date'):
            view.check_response_data({'handle': 'foo'})

    def test_base_response_template_view(self):
        view = BaseResponseTemplateView()
        self._assert_response_data(view)
        view.check_response_data(self.response_data)

    def test_custom_email_view(self):
        view = CustomEmailView()
        self._assert_response_data(view)
        data = {'send_to': 'custom_email'}
        data.update(self.response_data)
        with self.assertRaisesMessage(ResponseDataKeyMissing, 'custom_email'):
            view.check_response_data(data)
        data['custom_email'] = 'foo@foo'
        view.check_response_data(data)
        data = {'lock_type': 'transfer'}
        data.update(self.response_data)
        view.check_response_data(data)
        data = {'send_to': 'email_in_registry'}
        data.update(self.response_data)
        with self.assertRaisesMessage(ResponseDataKeyMissing, 'lock_type'):
            view.check_response_data(data)

    def test_notarized_letter_view(self):
        view = NotarizedLetterView()
        self._assert_response_data(view)
        with self.assertRaisesMessage(ResponseDataKeyMissing, 'send_to, block_unblock_action_type'):
            view.check_response_data(self.response_data)
        data = {'send_to': 'custom_email'}
        data.update(self.response_data)
        view.check_response_data(data)
        data = {'block_unblock_action_type': 'block'}
        data.update(self.response_data)
        view.check_response_data(data)
