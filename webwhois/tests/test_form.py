#
# Copyright (C) 2015-2020  CZ.NIC, z. s. p. o.
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
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from fred_idl.Registry.Whois import OBJECT_NOT_FOUND

from webwhois.forms import BlockObjectForm, SendPasswordForm, UnblockObjectForm, WhoisForm
from webwhois.forms.public_request import ConfirmationMethod, DeliveryType, PublicRequestBaseForm
from webwhois.tests.utils import TEMPLATES, apply_patch
from webwhois.utils import WHOIS


@override_settings(TEMPLATES=TEMPLATES)
class TestWhoisForm(SimpleTestCase):

    def test_is_valid(self):
        form = WhoisForm({"handle": "foo"})
        self.assertEqual(form.errors, {})

    def test_field_is_required(self):
        form = WhoisForm({"handle": None})
        self.assertEqual(form.errors, {'handle': ['This field is required.']})
        form = WhoisForm({"handle": ""})
        self.assertEqual(form.errors, {'handle': ['This field is required.']})

    def test_max_length(self):
        form = WhoisForm({"handle": "o" * 256})
        self.assertEqual(form.errors, {'handle': ['Ensure this value has at most 255 characters (it has 256).']})

    def test_cleaned_data(self):
        form = WhoisForm({"handle": "  foo  "})
        self.assertEqual(form.errors, {})
        self.assertEqual(form.cleaned_data, {"handle": "foo"})


@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestWhoisFormView(SimpleTestCase):

    def setUp(self):
        spec = ('get_contact_by_handle', 'get_domain_by_handle', 'get_keyset_by_handle',
                'get_nsset_by_handle', 'get_registrar_by_handle')
        apply_patch(self, patch.object(WHOIS, 'client', spec=spec))
        self.LOGGER = apply_patch(self, patch("webwhois.views.base.LOGGER"))

    def test_handle_required(self):
        response = self.client.post(reverse("webwhois:form_whois"))
        self.assertEqual(response.context["form"].errors, {'handle': ['This field is required.']})
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(WHOIS.mock_calls, [])

    def test_handle_invalid(self):
        response = self.client.post(reverse("webwhois:form_whois"), {"handle": "a" * 256})
        self.assertEqual(response.context["form"].errors, {'handle': [
            'Ensure this value has at most 255 characters (it has 256).']})
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(WHOIS.mock_calls, [])

    def test_handle_pattern(self):
        response = self.client.post(reverse("webwhois:form_whois"), {"handle": "a%3Fx"})
        self.assertRedirects(response, reverse("webwhois:registry_object_type", kwargs={"handle": "a%3Fx"}),
                             fetch_redirect_response=False)
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(WHOIS.mock_calls, [])

    def test_valid_handle(self):
        WHOIS.get_contact_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_nsset_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_keyset_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_registrar_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_domain_by_handle.side_effect = OBJECT_NOT_FOUND
        response = self.client.post(reverse("webwhois:form_whois"), {"handle": " mycontact "})
        self.assertRedirects(response, reverse("webwhois:registry_object_type", kwargs={"handle": "mycontact"}),
                             fetch_redirect_response=False)
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(WHOIS.mock_calls, [])

    def test_get_form(self):
        response = self.client.get(reverse("webwhois:form_whois"), {"handle": " mycontact "})
        self.assertContains(response, '<label for="id_handle">Domain (without <em>www.</em> prefix)'
                            ' / Handle:</label>', html=True)
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(WHOIS.mock_calls, [])


class TestPublicRequestBaseForm(SimpleTestCase):
    """Test `PublicRequestBaseForm` class."""

    def test_clean_confirmation_method(self):
        form = PublicRequestBaseForm({'confirmation_method': 'signed_email'})
        form.is_valid()
        self.assertEqual(form.cleaned_data['confirmation_method'], ConfirmationMethod.SIGNED_EMAIL)

    def test_clean_confirmation_method_empty(self):
        form = PublicRequestBaseForm({})
        form.is_valid()
        self.assertIsNone(form.cleaned_data['confirmation_method'])


class TestSendPasswordForm(SimpleTestCase):

    def test_is_valid(self):
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        })
        self.assertEqual(form.errors, {})
        self.assertEqual(form.cleaned_data, {
            'object_type': 'domain',
            'handle': 'foo.cz',
            'send_to': DeliveryType('email_in_registry', ""),
            'confirmation_method': ConfirmationMethod.SIGNED_EMAIL,
        })

    def test_field_is_required(self):
        form = SendPasswordForm({})
        self.assertEqual(form.errors, {
            'object_type': ['This field is required.'],
            'handle': ['This field is required.'],
            'send_to': ['This field is required.'],
        })

    def test_max_length(self):
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "o" * 256,
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        })
        self.assertEqual(form.errors, {'handle': ['Ensure this value has at most 255 characters (it has 256).']})

    def test_stripped_handle(self):
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "  foo  ",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
        })
        self.assertEqual(form.errors, {})
        self.assertEqual(form.cleaned_data["handle"], "foo")

    def test_enum_types(self):
        form = SendPasswordForm({
            "object_type": "foo",
            "handle": "foo.cz",
            "confirmation_method": "foo",
            "send_to_0": "foo",
        })
        self.assertEqual(form.errors, {
            'confirmation_method': ['Select a valid choice. foo is not one of the available choices.'],
            'object_type': ['Select a valid choice. foo is not one of the available choices.'],
            'send_to': ['Select a valid choice. foo is not one of the available choices.'],
        })

    def test_invalid_custom_email(self):
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
            "send_to_1": "foo",
        })
        self.assertEqual(form.errors, {'send_to': ['Enter a valid email address.']})

    def test_custom_email_and_sent_to_registry(self):
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to_0": "email_in_registry",
            "send_to_1": "foo@foo.off",
        })
        self.assertEqual(form.errors, {
            'send_to': ['Option "Send to email in registry" is incompatible with custom email. '
                        'Please choose one of the two options.']
        })

    def test_sent_to_custom_email(self):
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to_0": "custom_email",
        })
        self.assertEqual(form.errors, {
            'send_to': ['Custom email is required as "Send to custom email" option is selected. Please fill it in.']
        })

    def test_notarized_letter_send_to_registry(self):
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "notarized_letter",
            "send_to_0": "email_in_registry",
            "send_to_1": "",
        })
        self.assertEqual(form.errors, {
            '__all__': ['Letter with officially verified signature can be sent only to the custom email. '
                        'Please select "Send to custom email" and enter it.']
        })

    def test_notarized_letter_without_custom_email(self):
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "notarized_letter",
            "send_to_0": "custom_email",
        })
        self.assertEqual(form.errors, {
            'send_to': ['Custom email is required as "Send to custom email" option is selected. Please fill it in.']
        })

    def test_notarized_letter(self):
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "notarized_letter",
            "send_to_0": "custom_email",
            "send_to_1": "foo@foo.off",
        })
        self.assertEqual(form.errors, {})
        self.assertEqual(form.cleaned_data, {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": ConfirmationMethod.NOTARIZED_LETTER,
            "send_to": DeliveryType("custom_email", "foo@foo.off"),
        })


class BlockUnblockFormMixin(object):

    def test_is_valid(self: SimpleTestCase):
        form = self.form_class({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "lock_type": "transfer",
        })
        self.assertEqual(form.errors, {})
        self.assertEqual(form.cleaned_data, {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": ConfirmationMethod.SIGNED_EMAIL,
            "lock_type": "transfer",
        })

    def test_field_is_required(self: SimpleTestCase):
        form = self.form_class({})
        self.assertEqual(form.errors, {
            'object_type': ['This field is required.'],
            'handle': ['This field is required.'],
            'lock_type': ['This field is required.'],
        })

    def test_max_length(self: SimpleTestCase):
        form = self.form_class({
            "object_type": "domain",
            "handle": "o" * 256,
            "confirmation_method": "signed_email",
            "lock_type": "transfer",
        })
        self.assertEqual(form.errors, {'handle': ['Ensure this value has at most 255 characters (it has 256).']})

    def test_stripped_handle(self: SimpleTestCase):
        form = self.form_class({
            "object_type": "domain",
            "handle": "  foo  ",
            "confirmation_method": "signed_email",
            "lock_type": "transfer",
        })
        self.assertEqual(form.errors, {})
        self.assertEqual(form.cleaned_data["handle"], "foo")

    def test_enum_types(self: SimpleTestCase):
        form = self.form_class({
            "object_type": "foo",
            "handle": "foo.cz",
            "confirmation_method": "foo",
            "lock_type": "foo",
        })
        self.assertEqual(form.errors, {
            'confirmation_method': ['Select a valid choice. foo is not one of the available choices.'],
            'object_type': ['Select a valid choice. foo is not one of the available choices.'],
            'lock_type': ['Select a valid choice. foo is not one of the available choices.'],
        })

    def test_is_valid_notarized_letter_transfer(self: SimpleTestCase):
        form = self.form_class({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "notarized_letter",
            "lock_type": "transfer",
        })
        self.assertEqual(form.errors, {})
        self.assertEqual(form.cleaned_data, {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": ConfirmationMethod.NOTARIZED_LETTER,
            "lock_type": "transfer",
        })

    def test_is_valid_notarized_letter_all(self: SimpleTestCase):
        form = self.form_class({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "notarized_letter",
            "lock_type": "all",
        })
        self.assertEqual(form.errors, {})
        self.assertEqual(form.cleaned_data, {
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": ConfirmationMethod.NOTARIZED_LETTER,
            "lock_type": "all",
        })


class TestBlockObjectForm(BlockUnblockFormMixin, SimpleTestCase):
    form_class = BlockObjectForm


class TestUnblockObjectForm(BlockUnblockFormMixin, SimpleTestCase):
    form_class = UnblockObjectForm
