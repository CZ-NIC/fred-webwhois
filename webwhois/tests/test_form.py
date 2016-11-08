from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from mock import call, patch

from webwhois.forms import WhoisForm
from webwhois.tests.utils import WebwhoisAssertMixin, apply_patch
from webwhois.utils import WHOIS_MODULE


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


class TestWhoisFormView(WebwhoisAssertMixin, SimpleTestCase):

    urls = 'webwhois.tests.urls'
    managed_zone_list = ("cz", "0.2.4.e164.arpa")

    def setUp(self):
        self.WHOIS = apply_patch(self, patch("webwhois.views.pages.WHOIS"))
        apply_patch(self, patch("webwhois.views.detail_contact.WHOIS", self.WHOIS))
        apply_patch(self, patch("webwhois.views.detail_domain.WHOIS", self.WHOIS))
        apply_patch(self, patch("webwhois.views.detail_keyset.WHOIS", self.WHOIS))
        apply_patch(self, patch("webwhois.views.detail_nsset.WHOIS", self.WHOIS))
        apply_patch(self, patch("webwhois.views.registrar.WHOIS", self.WHOIS))
        self.LOGGER = apply_patch(self, patch("webwhois.views.base.LOGGER"))

    def test_handle_required(self):
        self.WHOIS.get_managed_zone_list.return_value = self.managed_zone_list
        response = self.client.post(reverse("webwhois:form_whois"))
        self.assertEqual(response.context["form"].errors, {'handle': ['This field is required.']})
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(self.WHOIS.mock_calls, [call.get_managed_zone_list()])

    def test_handle_invalid(self):
        self.WHOIS.get_managed_zone_list.return_value = self.managed_zone_list
        response = self.client.post(reverse("webwhois:form_whois"), {"handle": "a" * 256})
        self.assertEqual(response.context["form"].errors, {'handle': [
            'Ensure this value has at most 255 characters (it has 256).']})
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(self.WHOIS.mock_calls, [call.get_managed_zone_list()])

    def test_handle_pattern(self):
        self.WHOIS.get_managed_zone_list.return_value = self.managed_zone_list
        response = self.client.post(reverse("webwhois:form_whois"), {"handle": "a%3Fx"})
        self.assertRedirects(response, reverse("webwhois:registry_object_type", kwargs={"handle": "a%3Fx"}),
                             fetch_redirect_response=False)
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(self.WHOIS.mock_calls, [])

    def test_valid_handle(self):
        self.WHOIS.get_contact_by_handle.side_effect = WHOIS_MODULE.OBJECT_NOT_FOUND
        self.WHOIS.get_nsset_by_handle.side_effect = WHOIS_MODULE.OBJECT_NOT_FOUND
        self.WHOIS.get_keyset_by_handle.side_effect = WHOIS_MODULE.OBJECT_NOT_FOUND
        self.WHOIS.get_registrar_by_handle.side_effect = WHOIS_MODULE.OBJECT_NOT_FOUND
        self.WHOIS.get_domain_by_handle.side_effect = WHOIS_MODULE.OBJECT_NOT_FOUND
        response = self.client.post(reverse("webwhois:form_whois"), {"handle": " mycontact "})
        self.assertRedirects(response, reverse("webwhois:registry_object_type", kwargs={"handle": "mycontact"}),
                             fetch_redirect_response=False)
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(self.WHOIS.mock_calls, [])

    def test_get_form(self):
        self.WHOIS.get_managed_zone_list.return_value = self.managed_zone_list
        response = self.client.get(reverse("webwhois:form_whois"), {"handle": " mycontact "})
        self.assertXpathEqual(response, "//ul[@class='managed-zones']/li", self.managed_zone_list,
                              transform=self.transform_to_text)
        self.assertXpathEqual(response, "//span[@class='whois-search-engines']/a", [
            'WHOIS.COM Lookup', 'IANA WHOIS Service'
        ], transform=self.transform_to_text)
        self.assertContains(response, '<label for="id_handle">Domain (without <em>www.</em> prefix)'
                            ' / Handle:</label>', html=True)
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(self.WHOIS.mock_calls, [call.get_managed_zone_list()])
