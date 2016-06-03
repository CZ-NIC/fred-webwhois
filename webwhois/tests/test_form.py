from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from mock import patch

from webwhois.tests.utils import CorbaInitMixin, WebwhoisAssertMixin, apply_patch


class TestWhoisFormView(WebwhoisAssertMixin, CorbaInitMixin, SimpleTestCase):

    urls = 'webwhois.tests.urls'
    managed_zone_list = ("cz", "0.2.4.e164.arpa")

    def setUp(self):
        apply_patch(self, patch("webwhois.views.pages.CORBA", self.CORBA))
        self.WHOIS = apply_patch(self, patch("webwhois.views.pages.WHOIS"))

    def test_handle_required(self):
        self.WHOIS.get_managed_zone_list.return_value = self.managed_zone_list
        response = self.client.post(reverse("webwhois:form_whois"))
        self.assertEqual(response.context["form"].errors, {'handle': ['This field is required.']})

    def test_handle_invalid(self):
        self.WHOIS.get_managed_zone_list.return_value = self.managed_zone_list
        response = self.client.post(reverse("webwhois:form_whois"), {"handle": "a" * 256})
        self.assertEqual(response.context["form"].errors, {'handle': [
            'Ensure this value has at most 255 characters (it has 256).']})

    def test_valid_handle(self):
        self.WHOIS.get_contact_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        self.WHOIS.get_nsset_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        self.WHOIS.get_keyset_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        self.WHOIS.get_domain_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        response = self.client.post(reverse("webwhois:form_whois"), {"handle": " mycontact "})
        self.assertRedirects(response, reverse("webwhois:registry_object_type", kwargs={"handle": "mycontact"}))

    def test_get_form(self):
        self.WHOIS.get_managed_zone_list.return_value = self.managed_zone_list
        response = self.client.get(reverse("webwhois:form_whois"), {"handle": " mycontact "})
        self.assertXpathEqual(response, "//ul[@class='managed-zones']/li", self.managed_zone_list,
                              transform=self.transform_to_text)
        self.assertXpathEqual(response, "//span[@class='whois-search-engines']/a", [
            'WHOIS.COM Lookup', 'IANA WHOIS Service'
        ], transform=self.transform_to_text)
