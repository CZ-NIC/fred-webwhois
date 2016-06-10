#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.utils.formats import reset_format_cache
from mock import patch

from webwhois.tests.get_registry_objects import GetRegistryObjectMixin
from webwhois.tests.utils import CorbaInitMixin, WebwhoisAssertMixin, apply_patch


@override_settings(USE_TZ=True, TIME_ZONE='Europe/Prague', FORMAT_MODULE_PATH=None)
class TestObjectDetailView(WebwhoisAssertMixin, CorbaInitMixin, GetRegistryObjectMixin, SimpleTestCase):

    urls = 'webwhois.tests.urls'

    @classmethod
    def setUpClass(cls):
        super(TestObjectDetailView, cls).setUpClass()
        reset_format_cache()  # Reset cache with formats for date and time.

    def setUp(self):
        apply_patch(self, patch("webwhois.views.pages.CORBA", self.CORBA))
        self.WHOIS = apply_patch(self, patch("webwhois.views.pages.WHOIS"))
        self.RegWhois = self.CORBA.Registry.Whois

    def test_handle_not_found(self):
        self.WHOIS.get_contact_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        self.WHOIS.get_nsset_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        self.WHOIS.get_keyset_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        # Handle 'testhandle' for domain raises UNMANAGED_ZONE instead of OBJECT_NOT_FOUND.
        self.WHOIS.get_domain_by_handle.side_effect = self.CORBA.Registry.Whois.UNMANAGED_ZONE
        response = self.client.get(reverse("webwhois:registry_object_type", kwargs={"handle": "testhandle"}))
        self.assertContains(response, "Handle not found")
        self.assertContains(response, "No domain, contact or name server set matches <strong>testhandle</strong> query.")
        self.assertNotContains(response, 'Register this domain name?')

    def test_handle_with_dash_not_found(self):
        self.WHOIS.get_contact_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        self.WHOIS.get_nsset_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        self.WHOIS.get_keyset_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        # Handle 'testhandle' for domain raises UNMANAGED_ZONE instead of OBJECT_NOT_FOUND.
        self.WHOIS.get_domain_by_handle.side_effect = self.CORBA.Registry.Whois.UNMANAGED_ZONE
        response = self.client.get(reverse("webwhois:registry_object_type", kwargs={"handle": "-abc"}))
        self.assertContains(response, "Invalid domain name")
        self.assertContains(response, "No domain, contact or name server set matches <strong>-abc</strong> query.")
        self.assertNotContains(response, 'Register this domain name?')

    def test_handle_in_zone_not_found(self):
        self.WHOIS.get_contact_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        self.WHOIS.get_nsset_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        self.WHOIS.get_keyset_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        # Only valid domain name in zone raises OBJECT_NOT_FOUND.
        self.WHOIS.get_domain_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:registry_object_type", kwargs={"handle": "fred.cz"}))
        self.assertContains(response, "Handle not found")
        self.assertContains(response, "No domain, contact or name server set matches <strong>fred.cz</strong> query.")
        self.assertContains(response, 'Register this domain name?')

    def test_contact_not_found(self):
        self.WHOIS.get_contact_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "testhandle"}))
        self.assertContains(response, 'Contact not found')
        self.assertContains(response, 'No contact matches <strong>testhandle</strong> handle.')
        self.assertNotContains(response, 'Register this domain name?')

    def test_contact_invalid_handle(self):
        self.WHOIS.get_contact_by_handle.side_effect = self.CORBA.Registry.Whois.INVALID_HANDLE
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "testhandle"}))
        self.assertContains(response, "Invalid handle")
        self.assertContains(response, "<strong>testhandle</strong> is not a valid handle.")

    def test_multiple_entries(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact()
        self.WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        self.WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        self.WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        self.WHOIS.get_keyset_by_handle.return_value = self._get_keyset()
        self.WHOIS.get_domain_status_descriptions.return_value = self._get_domain_status()
        self.WHOIS.get_domain_by_handle.return_value = self._get_domain()
        response = self.client.get(reverse("webwhois:registry_object_type", kwargs={"handle": "testhandle.cz"}))
        self.assertContains(response, "Multiple entries found")
        self.assertCssSelectEqual(response, "#whois ul li", [
            'Keyset: testhandle.cz',
            'Domain: testhandle.cz',
            'Contact: testhandle.cz',
            'Nsset: testhandle.cz',
        ], transform=self.transform_to_text)

    def test_handle_contact_not_linked(self):
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=[])
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self.assertContains(response, "Contact details")
        self.assertContains(response, "Search results for handle <strong>mycontact</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Handle KONTAKT',
            'Sponsoring registrar REG-FRED_A Company A L.t.d.'
        ], transform=self.transform_to_text)

    def test_contact_not_linked(self):
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=[])
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self.assertContains(response, "Contact details")
        self.assertContains(response, "Search results for handle <strong>mycontact</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Handle KONTAKT',
            'Sponsoring registrar REG-FRED_A Company A L.t.d.'
        ], transform=self.transform_to_text)

    def test_contact_linked(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact()
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self.assertContains(response, "Contact details")
        self.assertContains(response, "Search results for handle <strong>mycontact</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Handle KONTAKT',
            'Organization Company L.t.d.',
            'Name Arnold Rimmer',
            'VAT number CZ456123789',
            'Identification type Personal ID',
            'Identification data 333777000',
            'E-mail rimmer@foo.foo',
            'Notify e-mail notify-rimmer@foo.foo',
            'Phone +420.728012345',
            'Fax +420.728023456',
            'Registered since 12/15/2015',
            'Created by registrar REG-FRED_A Company A L.t.d.',
            'Last update 12/16/2015',
            'Last transfer 12/17/2015',
            'Address Street 756/48, 12300 Prague, CZ',
            'Sponsoring registrar REG-FRED_A Company A L.t.d.',
            'Status Has relation to other records in the registry',
        ], transform=self.transform_to_text)

    def test_contact_with_not_disclosed(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(disclose=False)
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self.assertContains(response, "Contact details")
        self.assertContains(response, "Search results for handle <strong>mycontact</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Handle KONTAKT',
            'Organization Not disclosed',
            'Name Not disclosed',
            'VAT number Not disclosed',
            'Identification type Not disclosed',
            'Identification data Not disclosed',
            'E-mail Not disclosed',
            'Notify e-mail Not disclosed',
            'Phone Not disclosed',
            'Fax Not disclosed',
            'Registered since 12/15/2015',
            'Created by registrar REG-FRED_A Company A L.t.d.',
            'Last update 12/16/2015',
            'Last transfer 12/17/2015',
            'Address Not disclosed',
            'Sponsoring registrar REG-FRED_A Company A L.t.d.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)

    def test_contact_without_registrars_handle(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(creating_registrar_handle=None,
                                                                          sponsoring_registrar_handle=None)
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self.assertContains(response, "Contact details")
        self.assertContains(response, "Search results for handle <strong>mycontact</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Handle KONTAKT',
            'Organization Company L.t.d.',
            'Name Arnold Rimmer',
            'VAT number CZ456123789',
            'Identification type Personal ID',
            'Identification data 333777000',
            'E-mail rimmer@foo.foo',
            'Notify e-mail notify-rimmer@foo.foo',
            'Phone +420.728012345',
            'Fax +420.728023456',
            'Registered since 12/15/2015',
            'Created by registrar',
            'Last update 12/16/2015',
            'Last transfer 12/17/2015',
            'Address Street 756/48, 12300 Prague, CZ',
            'Sponsoring registrar',
            'Status Has relation to other records in the registry',
        ], transform=self.transform_to_text)

    def test_contact_with_ssn_type_birthday(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(
            identification=self.RegWhois.DisclosableContactIdentification(value=self.RegWhois.ContactIdentification(
                identification_type='BIRTHDAY', identification_data='2000-06-28'), disclose=True))
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self.assertContains(response, "Contact details")
        self.assertContains(response, "Search results for handle <strong>mycontact</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Handle KONTAKT',
            'Organization Company L.t.d.',
            'Name Arnold Rimmer',
            'VAT number CZ456123789',
            'Identification type Birth day',
            'Identification data June 28, 2000',
            'E-mail rimmer@foo.foo',
            'Notify e-mail notify-rimmer@foo.foo',
            'Phone +420.728012345',
            'Fax +420.728023456',
            'Registered since 12/15/2015',
            'Created by registrar REG-FRED_A Company A L.t.d.',
            'Last update 12/16/2015',
            'Last transfer 12/17/2015',
            'Address Street 756/48, 12300 Prague, CZ',
            'Sponsoring registrar REG-FRED_A Company A L.t.d.',
            'Status Has relation to other records in the registry',
        ], transform=self.transform_to_text)

    def test_contact_with_invalid_birthday_value(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(
            identification=self.RegWhois.DisclosableContactIdentification(value=self.RegWhois.ContactIdentification(
                identification_type='BIRTHDAY', identification_data='FOO'), disclose=True))
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self.assertCssSelectEqual(response, ".contact .ident-value", ['FOO'], transform=self.transform_to_text)

    def test_contact_verification_failed(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=["linked", "contactFailedManualVerification"])
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self.assertXpathEqual(response, "//th[text()='Contact verification status']/../td", [
            'Contact has failed the verification by CZ.NIC customer support'
        ], transform=self.transform_to_text)
        self.assertXpathEqual(response, "//img[@alt='contactFailedManualVerification']/@src", [
            '/static/webwhois/img/icon-red-cross.gif'])

    def test_contact_verification_in_manual(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=["linked", "contactInManualVerification"])
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self.assertXpathEqual(response, "//th[text()='Contact verification status']/../td", [
            'Contact is being verified by CZ.NIC customer support'
        ], transform=self.transform_to_text)
        self.assertXpathEqual(response, "//img[@alt='contactInManualVerification']/@src", [
            '/static/webwhois/img/icon-orange-cross.gif'])

    def test_contact_verification_ok(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=["linked", "validatedContact"])
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self.assertXpathEqual(response, "//th[text()='Contact verification status']/../td", [
            'Contact is validated'
        ], transform=self.transform_to_text)
        self.assertXpathEqual(response, "//img[@alt='validatedContact']/@src", [
            '/static/webwhois/img/icon-yes.gif'])

    def test_nsset_not_found(self):
        self.WHOIS.get_nsset_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:detail_nsset", kwargs={"handle": "mynssid"}))
        self.assertContains(response, 'Name server set not found')
        self.assertContains(response, 'No name server set matches <strong>mynssid</strong> handle.')
        self.assertNotContains(response, 'Register this domain name?')

    def test_nsset_invalid_handle(self):
        self.WHOIS.get_nsset_by_handle.side_effect = self.CORBA.Registry.Whois.INVALID_HANDLE
        response = self.client.get(reverse("webwhois:detail_nsset", kwargs={"handle": "mynssid"}))
        self.assertContains(response, "Invalid handle")
        self.assertContains(response, "<strong>mynssid</strong> is not a valid handle.")
        self.assertNotContains(response, 'Register this domain name?')

    def test_nsset(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact()
        self.WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        self.WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_nsset", kwargs={"handle": "mynssid"}))
        self.assertContains(response, "Name server set (DNS) details")
        self.assertContains(response, "Search results for handle <strong>mynssid</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Name server set NSSET-1',
            'Name server a.ns.nic.cz 194.0.12.1',
            'Name server b.ns.nic.cz 194.0.13.1',
            'Technical contact KONTAKT Company L.t.d.',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)

    def test_nsset_fqds_idna(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact()
        self.WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        self.WHOIS.get_nsset_by_handle.return_value = self._get_nsset(fqdn1='xn--hkyrky-ptac70bc.cz',
                                                                      fqdn2='xn--frd-cma.cz')
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_nsset", kwargs={"handle": "mynssid"}))
        self.assertContains(response, "Name server set (DNS) details")
        self.assertContains(response, "Search results for handle <strong>mynssid</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Name server set NSSET-1',
            u'Name server háčkyčárky.cz 194.0.12.1',
            u'Name server fréd.cz 194.0.13.1',
            'Technical contact KONTAKT Company L.t.d.',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)

    @override_settings(USE_TZ=False, TIME_ZONE='UTC')
    def test_nsset_witout_zone(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact()
        self.WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        self.WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_nsset", kwargs={"handle": "mynssid"}))
        self.assertContains(response, "Name server set (DNS) details")
        self.assertContains(response, "Search results for handle <strong>mynssid</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Name server set NSSET-1',
            'Name server a.ns.nic.cz 194.0.12.1',
            'Name server b.ns.nic.cz 194.0.13.1',
            'Technical contact KONTAKT Company L.t.d.',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 6:18 p.m.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)

    def test_nsset_with_contact_no_organization(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(
            organization=self.RegWhois.DisclosableString(value='', disclose=True))
        self.WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        self.WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_nsset", kwargs={"handle": "mynssid"}))
        self.assertContains(response, "Name server set (DNS) details")
        self.assertContains(response, "Search results for handle <strong>mynssid</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Name server set NSSET-1',
            'Name server a.ns.nic.cz 194.0.12.1',
            'Name server b.ns.nic.cz 194.0.13.1',
            'Technical contact KONTAKT Arnold Rimmer',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)

    def test_keyset_not_found(self):
        self.WHOIS.get_keyset_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:detail_keyset", kwargs={"handle": "mykeysid"}))
        self.assertContains(response, 'Key server set not found')
        self.assertContains(response, 'No key set matches <strong>mykeysid</strong> handle.')
        self.assertNotContains(response, 'Register this domain name?')

    def test_keyset_invalid_handle(self):
        self.WHOIS.get_keyset_by_handle.side_effect = self.CORBA.Registry.Whois.INVALID_HANDLE
        response = self.client.get(reverse("webwhois:detail_keyset", kwargs={"handle": "mykeysid"}))
        self.assertContains(response, "Invalid handle")
        self.assertContains(response, "<strong>mykeysid</strong> is not a valid handle.")
        self.assertNotContains(response, 'Register this domain name?')

    def test_keyset(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact()
        self.WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        self.WHOIS.get_keyset_by_handle.return_value = self._get_keyset()
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_keyset", kwargs={"handle": "mykeysid"}))
        self.assertContains(response, "Key set details")
        self.assertContains(response, "Search results for handle <strong>mykeysid</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Key set KEYSID-1',
            'DNS Key Flags: 257 Protocol: 3 Algorithm: 5 [alg] Key: AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxW EA4RJ9Ao6LCWheg8',
            'Technical contact KONTAKT Company L.t.d.',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)

    def test_keyset_with_contact_no_organization(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(
            organization=self.RegWhois.DisclosableString(value='', disclose=True))
        self.WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        self.WHOIS.get_keyset_by_handle.return_value = self._get_keyset()
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_keyset", kwargs={"handle": "mykeysid"}))
        self.assertContains(response, "Key set details")
        self.assertContains(response, "Search results for handle <strong>mykeysid</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Key set KEYSID-1',
            'DNS Key Flags: 257 Protocol: 3 Algorithm: 5 [alg] Key: AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxW EA4RJ9Ao6LCWheg8',
            'Technical contact KONTAKT Arnold Rimmer',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)

    def test_domain_not_found(self):
        self.WHOIS.get_domain_by_handle.side_effect = self.CORBA.Registry.Whois.OBJECT_NOT_FOUND
        self.WHOIS.get_managed_zone_list.return_value = ['cz', '0.2.4.e164.arpa']
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.cz"}))
        self.assertContains(response, 'Domain not found')
        self.assertContains(response, 'No domain matches <strong>fred.cz</strong> handle.')
        self.assertContains(response, 'Register this domain name?')

    def _mocks_for_domain_detail(self, handle=None):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact()
        self.WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        self.WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        self.WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        self.WHOIS.get_keyset_by_handle.return_value = self._get_keyset()
        self.WHOIS.get_domain_status_descriptions.return_value = self._get_domain_status()
        self.WHOIS.get_domain_by_handle.return_value = self._get_domain(handle=handle) if handle else self._get_domain()
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()

    def test_domain(self):
        self._mocks_for_domain_detail()
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.cz"}))
        self.assertContains(response, "Domain name details")
        self.assertContains(response, "Search results for handle <strong>fred.cz</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Domain name fred.cz',
            'Registered since 12/09/2015',
            'Last update date 12/10/2015',
            'Expiration date 12/09/2018',
            'Holder KONTAKT Company L.t.d.',
            'Administrative contact KONTAKT Company L.t.d.',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Secured by DNSSEC',
            'Status Deletion forbidden Update forbidden',
            'Name server set NSSET-1',
            'Name server a.ns.nic.cz 194.0.12.1',
            'Name server b.ns.nic.cz 194.0.13.1',
            'Technical contact KONTAKT Company L.t.d.',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry',
            'Key set KEYSID-1',
            'DNS Key Flags: 257 Protocol: 3 Algorithm: 5 [alg] Key: AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxW EA4RJ9Ao6LCWheg8',
            'Technical contact KONTAKT Company L.t.d.',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)

    def test_domain_with_contact_no_organization(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(
            organization=self.RegWhois.DisclosableString(value='', disclose=True))
        self.WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        self.WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        self.WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        self.WHOIS.get_keyset_by_handle.return_value = self._get_keyset()
        self.WHOIS.get_domain_status_descriptions.return_value = self._get_domain_status()
        self.WHOIS.get_domain_by_handle.return_value = self._get_domain()
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.cz"}))
        self.assertContains(response, "Domain name details")
        self.assertContains(response, "Search results for handle <strong>fred.cz</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Domain name fred.cz',
            'Registered since 12/09/2015',
            'Last update date 12/10/2015',
            'Expiration date 12/09/2018',
            'Holder KONTAKT Arnold Rimmer',
            'Administrative contact KONTAKT Arnold Rimmer',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Secured by DNSSEC',
            'Status Deletion forbidden Update forbidden',
            'Name server set NSSET-1',
            'Name server a.ns.nic.cz 194.0.12.1',
            'Name server b.ns.nic.cz 194.0.13.1',
            'Technical contact KONTAKT Arnold Rimmer',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry',
            'Key set KEYSID-1',
            'DNS Key Flags: 257 Protocol: 3 Algorithm: 5 [alg] Key: AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxW EA4RJ9Ao6LCWheg8',
            'Technical contact KONTAKT Arnold Rimmer',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)

    def test_domain_without_nsset_and_keyset(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact()
        self.WHOIS.get_domain_status_descriptions.return_value = self._get_domain_status()
        self.WHOIS.get_domain_by_handle.return_value = self._get_domain(nsset_handle=None, keyset_handle=None)
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.cz"}))
        self.assertContains(response, "Domain name details")
        self.assertContains(response, "Search results for handle <strong>fred.cz</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Domain name fred.cz',
            'Registered since 12/09/2015',
            'Last update date 12/10/2015',
            'Expiration date 12/09/2018',
            'Holder KONTAKT Company L.t.d.',
            'Administrative contact KONTAKT Company L.t.d.',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Secured by DNSSEC',
            'Status Deletion forbidden Update forbidden',
        ], transform=self.transform_to_text)

    def test_domain_unmanaged_zone(self):
        self.WHOIS.get_domain_by_handle.side_effect = self.CORBA.Registry.Whois.UNMANAGED_ZONE
        self.WHOIS.get_managed_zone_list.return_value = ['cz', '0.2.4.e164.arpa']
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.com"}))
        self.assertContains(response, 'Unmanaged zone')
        self.assertContains(response, 'Domain <strong>fred.com</strong> cannot be found in the registry. You can search for domains in the these zones only:')
        self.assertNotContains(response, 'Register this domain name?')
        self.assertCssSelectEqual(response, "ul li", ['cz', '0.2.4.e164.arpa'], transform=self.transform_to_text)

    def test_domain_invalid_label(self):
        self.WHOIS.get_domain_by_handle.side_effect = self.CORBA.Registry.Whois.INVALID_LABEL
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fr:ed.com"}))
        self.assertContains(response, 'Invalid domain name')
        self.assertContains(response, 'Invalid domain name <strong>fr:ed.com</strong>.')
        self.assertNotContains(response, 'Register this domain name?')

    def test_domain_invalid_label_with_dash(self):
        self.WHOIS.get_domain_by_handle.side_effect = self.CORBA.Registry.Whois.INVALID_LABEL
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "-abc"}))
        self.assertContains(response, 'Invalid domain name')
        self.assertContains(response, 'Invalid domain name <strong>-abc</strong>.')
        self.assertNotContains(response, 'Register this domain name?')

    def test_domain_too_many_labels(self):
        self.WHOIS.get_domain_by_handle.side_effect = self.CORBA.Registry.Whois.TOO_MANY_LABELS
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "www.fred.cz"}))
        self.assertContains(response, "Incorrect input")
        self.assertContains(response, "Too many parts in the domain name <strong>www.fred.cz</strong>.")
        self.assertContains(response, "Enter only the name and the zone:")
        self.assertXpathEqual(response, "//a[text()='fred.cz']/@href", [reverse("webwhois:form_whois") + "?handle=fred.cz"])

    def test_idn_domain(self):
        self._mocks_for_domain_detail(handle="xn--frd-cma.cz")
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": u"fréd.cz"}))
        self.assertContains(response, u"Search results for handle <strong>fréd.cz</strong>:")
        self.assertCssSelectEqual(response, ".domain .handle", ["xn--frd-cma.cz"], transform=self.transform_to_text)
        self.assertCssSelectEqual(response, ".domain .idn-handle", [u"fréd.cz"], transform=self.transform_to_text)

    def test_idn_domain_punycode(self):
        self._mocks_for_domain_detail(handle="xn--frd-cma.cz")
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "xn--frd-cma.cz"}))
        self.assertContains(response, "Search results for handle <strong>xn--frd-cma.cz</strong>:")
        self.assertCssSelectEqual(response, ".domain .handle", ["xn--frd-cma.cz"], transform=self.transform_to_text)
        self.assertCssSelectEqual(response, ".domain .idn-handle", [u"fréd.cz"], transform=self.transform_to_text)


@override_settings(USE_TZ=True, TIME_ZONE='Europe/Prague', FORMAT_MODULE_PATH=None)
class TestContactDetailWithMojeid(WebwhoisAssertMixin, CorbaInitMixin, GetRegistryObjectMixin, SimpleTestCase):

    urls = 'webwhois.tests.urls'

    def setUp(self):
        apply_patch(self, patch("webwhois.views.pages.CORBA", self.CORBA))
        self.WHOIS = apply_patch(self, patch("webwhois.views.pages.WHOIS"))
        self.RegWhois = self.CORBA.Registry.Whois

    def test_button_mojeid(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact()
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_mojeid_contact", kwargs={"handle": "mycontact"}))
        self.assertXpathEqual(response, "//form[@action='%s']/input" % settings.WEBWHOIS_MOJEID_TRANSFER_ENDPOINT, [
            ('hidden', 'username', 'kontakt'),
            ('submit', None, 'Create mojeID from the domain registry')
        ], transform=lambda node: (node.attrib["type"], node.attrib.get("name"), node.attrib["value"]), normalize=False)
        self.assertXpathEqual(response, "count(//a[@href='%s?username=kontakt'])=1" % (
            settings.WEBWHOIS_MOJEID_REGISTRY_ENDPOINT), True)
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % settings.WEBWHOIS_MOJEID_LINK_WHY, ["Why mojeID"])

    def test_improper_handle_format(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(handle="MY.HANDLE")
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_mojeid_contact", kwargs={"handle": "MY.HANDLE"}))
        self.assertXpathEqual(response, "count(//form)=0", True)
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % settings.WEBWHOIS_MOJEID_LINK_WHY, [])

    def test_status_not_linked(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=[])
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_mojeid_contact", kwargs={"handle": "mycontact"}))
        self.assertXpathEqual(response, "//form[@action='%s']/input" % settings.WEBWHOIS_MOJEID_TRANSFER_ENDPOINT, [
            ('hidden', 'username', 'kontakt'),
            ('submit', None, 'Create mojeID from the domain registry')
        ], transform=lambda node: (node.attrib["type"], node.attrib.get("name"), node.attrib["value"]), normalize=False)
        self.assertXpathEqual(response, "count(//a[@href='%s?username=kontakt'])=1" % (
            settings.WEBWHOIS_MOJEID_REGISTRY_ENDPOINT), True)
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % settings.WEBWHOIS_MOJEID_LINK_WHY, ["Why mojeID"])

    def _do_test_statuses(self, statuses):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=statuses)
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_mojeid_contact", kwargs={"handle": "mycontact"}))
        self.assertXpathEqual(response, "count(//form)=0", True)
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % settings.WEBWHOIS_MOJEID_LINK_WHY, [])

    def test_status_mojeid_contact(self):
        self._do_test_statuses(["linked", "mojeidContact"])

    def test_status_server_transfer_prohibited(self):
        self._do_test_statuses(["linked", "serverTransferProhibited"])

    def test_status_server_update_prohibited(self):
        self._do_test_statuses(["linked", "serverUpdateProhibited"])

    def test_status_server_delete_prohibited(self):
        self._do_test_statuses(["linked", "serverDeleteProhibited"])

    def test_status_delete_candidate(self):
        self._do_test_statuses(["linked", "deleteCandidate"])

    def test_status_server_blocked(self):
        self._do_test_statuses(["linked", "serverBlocked"])


@override_settings(USE_TZ=True, TIME_ZONE='Europe/Prague', FORMAT_MODULE_PATH=None)
class TestDetailCss(WebwhoisAssertMixin, CorbaInitMixin, GetRegistryObjectMixin, SimpleTestCase):

    urls = 'webwhois.tests.urls'

    @classmethod
    def setUpClass(cls):
        super(TestDetailCss, cls).setUpClass()
        reset_format_cache()  # Reset cache with formats for date and time.

    def setUp(self):
        apply_patch(self, patch("webwhois.views.pages.CORBA", self.CORBA))
        self.WHOIS = apply_patch(self, patch("webwhois.views.pages.WHOIS"))
        self.RegWhois = self.CORBA.Registry.Whois

    def _assert_css(self, selector, result):
        self.assertCssSelectEqual(self._response, selector, [result], transform=self.transform_to_text)

    def test_contact(self):
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=["linked", "validatedContact"])
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        self._response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self._assert_css(".contact .handle", "KONTAKT")
        self._assert_css(".contact .organization", "Company L.t.d.")
        self._assert_css(".contact .full-name", "Arnold Rimmer")
        self._assert_css(".contact .vat-number", "CZ456123789")
        self._assert_css(".contact .ident-type", "Personal ID")
        self._assert_css(".contact .ident-value", "333777000")
        self._assert_css(".contact .email", "rimmer@foo.foo")
        self._assert_css(".contact .notify-email", "notify-rimmer@foo.foo")
        self._assert_css(".contact .phone", "+420.728012345")
        self._assert_css(".contact .fax", "+420.728023456")
        self._assert_css(".contact .registered-since", "12/15/2015")
        self._assert_css(".contact .creating-registrar", "REG-FRED_A Company A L.t.d.")
        self._assert_css(".contact .creating-registrar a", "REG-FRED_A")
        self._assert_css(".contact .last-update", "12/16/2015")
        self._assert_css(".contact .last-transfer", "12/17/2015")
        self._assert_css(".contact .address", "Street 756/48, 12300 Prague, CZ")
        self._assert_css(".contact .sponsoring-registrar", "REG-FRED_A Company A L.t.d.")
        self._assert_css(".contact .sponsoring-registrar a", "REG-FRED_A")
        self.assertCssSelectEqual(self._response, ".contact .status", ["linked,validatedContact"],
                                  transform=lambda node: node.attrib["data-codes"])

    def test_nsset(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact()
        self.WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        self.WHOIS.get_nsset_by_handle.return_value = self._get_nsset(statuses=["linked", "serverDeleteProhibited"])
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        self._response = self.client.get(reverse("webwhois:detail_nsset", kwargs={"handle": "mynssid"}))
        self._assert_css(".nsset .handle", "NSSET-1")
        self.assertCssSelectEqual(self._response, ".nsset .name-server", [
            "a.ns.nic.cz 194.0.12.1", "b.ns.nic.cz 194.0.13.1"], transform=self.transform_to_text)
        self.assertCssSelectEqual(self._response, ".nsset .name-server .dns_name", [
            "a.ns.nic.cz", "b.ns.nic.cz"], transform=self.transform_to_text)
        self._assert_css(".nsset .technical-contact", "KONTAKT Company L.t.d.")
        self._assert_css(".nsset .technical-contact a", "KONTAKT")
        self._assert_css(".nsset .sponsoring-registrar", "REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.")
        self._assert_css(".nsset .sponsoring-registrar a", "REG-FRED_A")
        self.assertCssSelectEqual(self._response, ".nsset .status", ["linked,serverDeleteProhibited"],
                                  transform=lambda node: node.attrib["data-codes"])

    def test_keyset(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.return_value = self._get_contact()
        self.WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        self.WHOIS.get_keyset_by_handle.return_value = self._get_keyset(statuses=["linked", "serverDeleteProhibited"])
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        self._response = self.client.get(reverse("webwhois:detail_keyset", kwargs={"handle": "mykeysid"}))
        self._assert_css(".keyset .handle", "KEYSID-1")
        self.assertCssSelectEqual(self._response, ".keyset .dns-key span:not(.label)", [
            '257', '3', '5', 'alg'], transform=self.transform_to_text)
        self._assert_css(".keyset .dns-key .dnskey", "AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxW EA4RJ9Ao6LCWheg8")
        self._assert_css(".keyset .technical-contact", "KONTAKT Company L.t.d.")
        self._assert_css(".keyset .technical-contact a", "KONTAKT")
        self._assert_css(".keyset .sponsoring-registrar", "REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.")
        self._assert_css(".keyset .sponsoring-registrar a", "REG-FRED_A")
        self.assertCssSelectEqual(self._response, ".keyset .status", ["linked,serverDeleteProhibited"],
                                  transform=lambda node: node.attrib["data-codes"])

    def test_domain(self):
        self.WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        self.WHOIS.get_contact_by_handle.side_effect = (
            self._get_contact(handle="HOLDER"),
            self._get_contact(handle="DOMAIN-ADMIN"),
            self._get_contact(handle="TECH-NSSET"),
            self._get_contact(handle="TECH-KEYSET"),
        )
        self.WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        self.WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        self.WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        self.WHOIS.get_keyset_by_handle.return_value = self._get_keyset(statuses=["linked", "serverUpdateProhibited"])
        self.WHOIS.get_domain_status_descriptions.return_value = self._get_domain_status()
        self.WHOIS.get_domain_by_handle.return_value = self._get_domain()
        self.WHOIS.get_registrar_by_handle.side_effect = (
            self._get_registrar(handle="REG-DOMAIN"),
            self._get_registrar(handle="REG-NSSET"),
            self._get_registrar(handle="REG-KEYSET"),
        )
        self._response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.cz"}))
        # domain
        self._assert_css(".domain .handle", "fred.cz")
        self._assert_css(".domain .registered-since", "12/09/2015")
        self._assert_css(".domain .last-update-date", "12/10/2015")
        self._assert_css(".domain .expiration-date", "12/09/2018")
        self._assert_css(".domain .holder", "HOLDER Company L.t.d.")
        self._assert_css(".domain .holder a", "HOLDER")
        self._assert_css(".domain .admins", "DOMAIN-ADMIN Company L.t.d.")
        self._assert_css(".domain .admins a", "DOMAIN-ADMIN")
        self._assert_css(".domain .sponsoring-registrar", "REG-DOMAIN Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.")
        self._assert_css(".domain .sponsoring-registrar a", "REG-DOMAIN")
        self.assertCssSelectEqual(self._response, ".domain .dnssec img", ["Yes"],
                                  transform=lambda node: node.attrib["alt"])
        self.assertCssSelectEqual(self._response, ".domain .status", ["serverDeleteProhibited,serverUpdateProhibited"],
                                  transform=lambda node: node.attrib["data-codes"])
        # nsset
        self._assert_css(".nsset .handle", "NSSET-1")
        self.assertCssSelectEqual(self._response, ".nsset .name-server", [
            "a.ns.nic.cz 194.0.12.1", "b.ns.nic.cz 194.0.13.1"], transform=self.transform_to_text)
        self.assertCssSelectEqual(self._response, ".nsset .name-server .dns_name", [
            "a.ns.nic.cz", "b.ns.nic.cz"], transform=self.transform_to_text)
        self._assert_css(".nsset .technical-contact", "TECH-NSSET Company L.t.d.")
        self._assert_css(".nsset .technical-contact a", "TECH-NSSET")
        self._assert_css(".nsset .sponsoring-registrar", "REG-NSSET Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.")
        self._assert_css(".nsset .sponsoring-registrar a", "REG-NSSET")
        self.assertCssSelectEqual(self._response, ".nsset .status", ["linked"],
                                  transform=lambda node: node.attrib["data-codes"])
        # keyset
        self._assert_css(".keyset .handle", "KEYSID-1")
        self.assertCssSelectEqual(self._response, ".keyset .dns-key span:not(.label)", [
            '257', '3', '5', 'alg'], transform=self.transform_to_text)
        self._assert_css(".keyset .dns-key .dnskey", "AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxW EA4RJ9Ao6LCWheg8")
        self._assert_css(".keyset .technical-contact", "TECH-KEYSET Company L.t.d.")
        self._assert_css(".keyset .technical-contact a", "TECH-KEYSET")
        self._assert_css(".keyset .sponsoring-registrar", "REG-KEYSET Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.")
        self._assert_css(".keyset .sponsoring-registrar a", "REG-KEYSET")
        self.assertCssSelectEqual(self._response, ".keyset .status", ["linked,serverUpdateProhibited"],
                                  transform=lambda node: node.attrib["data-codes"])
