#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.formats import reset_format_cache
from django.views import View
from fred_idl.ccReg import DateTimeType, DateType
from fred_idl.Registry.Whois import INVALID_HANDLE, INVALID_LABEL, OBJECT_NOT_FOUND, TOO_MANY_LABELS, UNMANAGED_ZONE, \
    ContactIdentification, DisclosableContactIdentification, DisclosableString
from mock import call, patch, sentinel

from webwhois.constants import STATUS_DELETE_CANDIDATE, STATUS_DELETE_PROHIBITED, STATUS_LINKED, \
    STATUS_MOJEID_CONTACT, STATUS_SERVER_BLOCKED, STATUS_TRANSFER_PROHIBITED, STATUS_UPDATE_PROHIBITED, \
    STATUS_VALIDATED, STATUS_VERIFICATION_FAILED, STATUS_VERIFICATION_IN_PROCESS
from webwhois.tests.get_registry_objects import GetRegistryObjectMixin
from webwhois.utils import WHOIS
from webwhois.views.base import RegistryObjectMixin
from webwhois.views.detail_keyset import KeysetDetailMixin
from webwhois.views.detail_nsset import NssetDetailMixin

from .utils import TEMPLATES, WebwhoisAssertMixin, apply_patch, make_keyset

WEBWHOIS_MOJEID_TRANSFER_ENDPOINT = "https://mojeid.cz/endpoint/"
WEBWHOIS_MOJEID_REGISTRY_ENDPOINT = "https://mojeid.cz/mogrify/preface/"
WEBWHOIS_MOJEID_LINK_WHY = "https://mojeid.cz/why/"
WEBWHOIS_DNSSEC_URL = "http://www.nic.cz/dnssec/"


@override_settings(USE_TZ=True, TIME_ZONE='Europe/Prague', FORMAT_MODULE_PATH=None, LANGUAGE_CODE='en',
                   CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}},
                   ROOT_URLCONF='webwhois.tests.urls', STATIC_URL='/static/')
class ObjectDetailMixin(WebwhoisAssertMixin, GetRegistryObjectMixin, SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super(ObjectDetailMixin, cls).setUpClass()
        reset_format_cache()  # Reset cache with formats for date and time.

    def setUp(self):
        spec = ('get_contact_by_handle', 'get_contact_status_descriptions',
                'get_domain_by_handle', 'get_domain_status_descriptions',
                'get_keyset_by_handle', 'get_keyset_status_descriptions', 'get_managed_zone_list',
                'get_nsset_by_handle', 'get_nsset_status_descriptions', 'get_registrar_by_handle')
        apply_patch(self, patch.object(WHOIS, 'client', spec=spec))
        self.LOGGER = apply_patch(self, patch("webwhois.views.base.LOGGER"))


@override_settings(TEMPLATES=TEMPLATES)
class TestResolveHandleType(ObjectDetailMixin):

    def test_handle_not_found(self):
        WHOIS.get_contact_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_nsset_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_keyset_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_registrar_by_handle.side_effect = OBJECT_NOT_FOUND
        # Handle 'testhandle' for domain raises UNMANAGED_ZONE instead of OBJECT_NOT_FOUND.
        WHOIS.get_domain_by_handle.side_effect = UNMANAGED_ZONE
        response = self.client.get(reverse("webwhois:registry_object_type", kwargs={"handle": "testhandle"}))
        self.assertContains(response, "Handle not found")
        self.assertContains(response,
                            "No domain, contact or name server set matches <strong>testhandle</strong> query.")
        self.assertNotContains(response, 'Register this domain name?')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'testhandle'), ('handleType', 'multiple'))),
            call.create_request().close(properties=[])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('testhandle'),
            call.get_nsset_by_handle('testhandle'),
            call.get_keyset_by_handle('testhandle'),
            call.get_registrar_by_handle('testhandle'),
            call.get_domain_by_handle('testhandle')
        ])

    def test_handle_with_dash_not_found(self):
        WHOIS.get_contact_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_nsset_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_keyset_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_registrar_by_handle.side_effect = OBJECT_NOT_FOUND
        # Handle 'testhandle' for domain raises UNMANAGED_ZONE instead of OBJECT_NOT_FOUND.
        WHOIS.get_domain_by_handle.side_effect = UNMANAGED_ZONE
        response = self.client.get(reverse("webwhois:registry_object_type", kwargs={"handle": "-abc"}))
        self.assertContains(response, "Handle not found")
        self.assertContains(response, "No domain, contact or name server set matches <strong>-abc</strong> query.")
        self.assertNotContains(response, 'Register this domain name?')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', '-abc'), ('handleType', 'multiple'))),
            call.create_request().close(properties=[('reason', 'IDNAError')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle(u'-abc'),
            call.get_nsset_by_handle(u'-abc'),
            call.get_keyset_by_handle(u'-abc'),
            call.get_registrar_by_handle(u'-abc')
        ])

    def test_handle_in_zone_not_found(self):
        WHOIS.get_contact_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_nsset_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_keyset_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_registrar_by_handle.side_effect = OBJECT_NOT_FOUND
        # Only valid domain name in zone raises OBJECT_NOT_FOUND.
        WHOIS.get_domain_by_handle.side_effect = OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:registry_object_type", kwargs={"handle": "fred.cz"}))
        self.assertContains(response, "Handle not found")
        self.assertContains(response, "No domain, contact or name server set matches <strong>fred.cz</strong> query.")
        self.assertContains(response, 'Register this domain name?')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'fred.cz'), ('handleType', 'multiple'))),
            call.create_request().close(properties=[])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('fred.cz'),
            call.get_nsset_by_handle('fred.cz'),
            call.get_keyset_by_handle('fred.cz'),
            call.get_registrar_by_handle('fred.cz'),
            call.get_domain_by_handle('fred.cz')
        ])

    def test_contact_not_found(self):
        WHOIS.get_contact_by_handle.side_effect = OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "testhandle"}))
        self.assertContains(response, 'Contact not found')
        self.assertContains(response, 'No contact matches <strong>testhandle</strong> handle.')
        self.assertNotContains(response, 'Register this domain name?')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'testhandle'), ('handleType', 'contact'))),
            call.create_request().close(properties=[])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_contact_by_handle('testhandle')])

    def test_contact_invalid_handle(self):
        WHOIS.get_contact_by_handle.side_effect = INVALID_HANDLE
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "testhandle"}))
        self.assertContains(response, "Invalid handle")
        self.assertContains(response, "<strong>testhandle</strong> is not a valid handle.")
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'testhandle'), ('handleType', 'contact'))),
            call.create_request().close(properties=[('reason', 'INVALID_HANDLE')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_contact_by_handle('testhandle')])

    def test_contact_invalid_handle_escaped(self):
        WHOIS.get_contact_by_handle.side_effect = INVALID_HANDLE
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "test<handle"}))
        self.assertContains(response, "Invalid handle")
        self.assertContains(response, "<strong>test&lt;handle</strong> is not a valid handle.")
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'test<handle'), ('handleType', 'contact'))),
            call.create_request().close(properties=[('reason', 'INVALID_HANDLE')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_contact_by_handle('test<handle')])

    def test_multiple_entries(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact()
        WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        WHOIS.get_keyset_by_handle.return_value = self._get_keyset()
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        WHOIS.get_domain_status_descriptions.return_value = self._get_domain_status()
        WHOIS.get_domain_by_handle.return_value = self._get_domain()
        response = self.client.get(reverse("webwhois:registry_object_type", kwargs={"handle": "testhandle.cz"}))
        self.assertContains(response, "Multiple entries found")
        self.assertCssSelectEqual(response, "#whois ul li", [
            'Keyset: testhandle.cz /whois/keyset/testhandle.cz/',
            'Domain: testhandle.cz /whois/domain/testhandle.cz/',
            'Contact: testhandle.cz /whois/contact/testhandle.cz/',
            'Registrar: testhandle.cz /whois/registrar/testhandle.cz/',
            'Nsset: testhandle.cz /whois/nsset/testhandle.cz/',
        ], transform=lambda node: "%s %s" % ("".join(node.xpath(".//text()")), ",".join(node.xpath("a/@href"))))
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'testhandle.cz'), ('handleType', 'multiple'))),
            call.create_request().close(properties=[
                ('foundType', 'keyset'),
                ('foundType', 'domain'),
                ('foundType', 'contact'),
                ('foundType', 'registrar'),
                ('foundType', 'nsset'),
            ])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('testhandle.cz'),
            call.get_nsset_by_handle('testhandle.cz'),
            call.get_keyset_by_handle('testhandle.cz'),
            call.get_registrar_by_handle('testhandle.cz'),
            call.get_domain_by_handle('testhandle.cz')
        ])

    def test_one_entry(self):
        WHOIS.get_contact_by_handle.return_value = self._get_contact()
        WHOIS.get_nsset_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_keyset_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_registrar_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_domain_by_handle.side_effect = UNMANAGED_ZONE
        response = self.client.get(reverse("webwhois:registry_object_type", kwargs={"handle": "testhandle"}))
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        WHOIS.get_registrar_by_handle.side_effect = None
        self.assertRedirects(response, reverse("webwhois:detail_contact", kwargs={"handle": "testhandle"}))


@override_settings(TEMPLATES=TEMPLATES)
class TestDetailContact(ObjectDetailMixin):

    def test_contact_not_found(self):
        WHOIS.get_contact_by_handle.side_effect = OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "testhandle"}))
        self.assertContains(response, 'Contact not found')
        self.assertContains(response, 'No contact matches <strong>testhandle</strong> handle.')
        self.assertNotContains(response, 'Register this domain name?')

    def test_contact_invalid_handle(self):
        WHOIS.get_contact_by_handle.side_effect = INVALID_HANDLE
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "testhandle"}))
        self.assertContains(response, "Invalid handle")
        self.assertContains(response, "<strong>testhandle</strong> is not a valid handle.")

    def test_contact_invalid_handle_escaped(self):
        WHOIS.get_contact_by_handle.side_effect = INVALID_HANDLE
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "test<handle"}))
        self.assertContains(response, "Invalid handle")
        self.assertContains(response, "<strong>test&lt;handle</strong> is not a valid handle.")

    def test_contact_not_linked(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=[])
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self.assertContains(response, "Contact details")
        self.assertContains(response, "Search results for handle <strong>mycontact</strong>:")
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mycontact'), ('handleType', 'contact'))),
            call.create_request().close(properties=[('foundType', 'contact')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('mycontact'),
            call.get_contact_status_descriptions('en'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_contact_linked(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact()
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
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
            'Email rimmer@foo.foo',
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
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mycontact'), ('handleType', 'contact'))),
            call.create_request().close(properties=[('foundType', 'contact')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('mycontact'),
            call.get_contact_status_descriptions('en'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_contact_with_not_disclosed(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(disclose=False)
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
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
            'Email Not disclosed',
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
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mycontact'), ('handleType', 'contact'))),
            call.create_request().close(properties=[('foundType', 'contact')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('mycontact'),
            call.get_contact_status_descriptions('en'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_contact_without_registrars_handle(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(creating_registrar_handle="",
                                                                     sponsoring_registrar_handle="")
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
            'Email rimmer@foo.foo',
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
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mycontact'), ('handleType', 'contact'))),
            call.create_request().close(properties=[('foundType', 'contact')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('mycontact'),
            call.get_contact_status_descriptions('en')
        ])

    def test_contact_with_ssn_type_birthday(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        ident = DisclosableContactIdentification(
            value=ContactIdentification(identification_type='BIRTHDAY', identification_data='2000-06-28'),
            disclose=True,
        )
        WHOIS.get_contact_by_handle.return_value = self._get_contact(identification=ident)
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
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
            'Email rimmer@foo.foo',
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
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mycontact'), ('handleType', 'contact'))),
            call.create_request().close(properties=[('foundType', 'contact')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('mycontact'),
            call.get_contact_status_descriptions('en'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_contact_with_invalid_birthday_value(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(
            identification=DisclosableContactIdentification(
                value=ContactIdentification(identification_type='BIRTHDAY', identification_data='FOO'),
                disclose=True))
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))
        self.assertCssSelectEqual(response, ".contact .ident-value", ['FOO'], transform=self.transform_to_text)
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mycontact'), ('handleType', 'contact'))),
            call.create_request().close(properties=[('foundType', 'contact')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('mycontact'),
            call.get_contact_status_descriptions('en'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_contact_verification_failed(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(
            statuses=[STATUS_LINKED, STATUS_VERIFICATION_FAILED],
        )
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))

        self.assertContains(response, "Contact details")
        self.assertXpathEqual(response, "//th[text()='Contact verification status']/../td", [
            'Contact has failed the verification by CZ.NIC customer support'
        ], transform=self.transform_to_text)
        verification_status = response.context["registry_objects"]['contact']['verification_status']
        self.assertEqual(verification_status[0]['code'], STATUS_VERIFICATION_FAILED)
        self.assertEqual(verification_status[0]['icon'], 'webwhois/img/icon-red-cross.gif')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mycontact'), ('handleType', 'contact'))),
            call.create_request().close(properties=[('foundType', 'contact')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('mycontact'),
            call.get_contact_status_descriptions('en'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_contact_verification_in_manual(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(
            statuses=[STATUS_LINKED, STATUS_VERIFICATION_IN_PROCESS])
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))

        self.assertContains(response, "Contact details")
        self.assertXpathEqual(response, "//th[text()='Contact verification status']/../td", [
            'Contact is being verified by CZ.NIC customer support'
        ], transform=self.transform_to_text)
        verification_status = response.context["registry_objects"]['contact']['verification_status']
        self.assertEqual(verification_status[0]['code'], STATUS_VERIFICATION_IN_PROCESS)
        self.assertEqual(verification_status[0]['icon'], 'webwhois/img/icon-orange-cross.gif')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mycontact'), ('handleType', 'contact'))),
            call.create_request().close(properties=[('foundType', 'contact')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('mycontact'),
            call.get_contact_status_descriptions('en'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_contact_verification_ok(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=[STATUS_LINKED, STATUS_VALIDATED])
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_contact", kwargs={"handle": "mycontact"}))

        self.assertContains(response, "Contact details")
        self.assertXpathEqual(response, "//th[text()='Contact verification status']/../td", [
            'Contact is validated'
        ], transform=self.transform_to_text)
        verification_status = response.context["registry_objects"]['contact']['verification_status']
        self.assertEqual(verification_status[0]['code'], STATUS_VALIDATED)
        self.assertEqual(verification_status[0]['icon'], 'webwhois/img/icon-yes.gif')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mycontact'), ('handleType', 'contact'))),
            call.create_request().close(properties=[('foundType', 'contact')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('mycontact'),
            call.get_contact_status_descriptions('en'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])


@override_settings(TEMPLATES=TEMPLATES)
class TestDetailNsset(ObjectDetailMixin):

    def test_nsset_not_found(self):
        WHOIS.get_nsset_by_handle.side_effect = OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:detail_nsset", kwargs={"handle": "mynssid"}))
        self.assertContains(response, 'Name server set not found')
        self.assertContains(response, 'No name server set matches <strong>mynssid</strong> handle.')
        self.assertNotContains(response, 'Register this domain name?')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mynssid'), ('handleType', 'nsset'))),
            call.create_request().close(properties=[])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_nsset_by_handle('mynssid')])

    def test_nsset_invalid_handle(self):
        WHOIS.get_nsset_by_handle.side_effect = INVALID_HANDLE
        response = self.client.get(reverse("webwhois:detail_nsset", kwargs={"handle": "mynssid"}))
        self.assertContains(response, "Invalid handle")
        self.assertContains(response, "<strong>mynssid</strong> is not a valid handle.")
        self.assertNotContains(response, 'Register this domain name?')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mynssid'), ('handleType', 'nsset'))),
            call.create_request().close(properties=[('reason', 'INVALID_HANDLE')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_nsset_by_handle('mynssid')])

    def test_nsset(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact()
        WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
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
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mynssid'), ('handleType', 'nsset'))),
            call.create_request().close(properties=[('foundType', 'nsset')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_nsset_by_handle('mynssid'),
            call.get_nsset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_append_nsset_related(self):
        nsset = self._get_nsset()
        admin = self._get_contact()
        registrar = self._get_registrar()
        WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        WHOIS.get_contact_by_handle.return_value = admin
        WHOIS.get_registrar_by_handle.return_value = registrar
        data = {"detail": nsset}
        NssetDetailMixin.append_nsset_related(data)
        self.assertEqual(data, {
            "detail": nsset,
            "admins": [admin],
            "registrar": registrar,
            "status_descriptions": ['Has relation to other records in the registry'],
        })

    def test_nsset_fqds_idna(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact()
        WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        WHOIS.get_nsset_by_handle.return_value = self._get_nsset(fqdn1='xn--hkyrky-ptac70bc.cz', fqdn2='xn--frd-cma.cz')
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
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
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mynssid'), ('handleType', 'nsset'))),
            call.create_request().close(properties=[('foundType', 'nsset')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_nsset_by_handle('mynssid'),
            call.get_nsset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    @override_settings(USE_TZ=False, TIME_ZONE='UTC')
    def test_nsset_witout_zone(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact()
        WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
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
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mynssid'), ('handleType', 'nsset'))),
            call.create_request().close(properties=[('foundType', 'nsset')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_nsset_by_handle('mynssid'),
            call.get_nsset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_nsset_with_contact_no_organization(self):
        "Test for set disclose of organization to True."
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(
            organization=DisclosableString(value='', disclose=True))
        WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
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
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mynssid'), ('handleType', 'nsset'))),
            call.create_request().close(properties=[('foundType', 'nsset')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_nsset_by_handle('mynssid'),
            call.get_nsset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])


@override_settings(TEMPLATES=TEMPLATES)
class TestDetailKeyset(ObjectDetailMixin):

    def test_keyset_not_found(self):
        WHOIS.get_keyset_by_handle.side_effect = OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:detail_keyset", kwargs={"handle": "mykeysid"}))
        self.assertContains(response, 'Key server set not found')
        self.assertContains(response, 'No key set matches <strong>mykeysid</strong> handle.')
        self.assertNotContains(response, 'Register this domain name?')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mykeysid'), ('handleType', 'keyset'))),
            call.create_request().close(properties=[])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_keyset_by_handle(u'mykeysid')])

    def test_keyset_invalid_handle(self):
        WHOIS.get_keyset_by_handle.side_effect = INVALID_HANDLE
        response = self.client.get(reverse("webwhois:detail_keyset", kwargs={"handle": "mykeysid"}))
        self.assertContains(response, "Invalid handle")
        self.assertContains(response, "<strong>mykeysid</strong> is not a valid handle.")
        self.assertNotContains(response, 'Register this domain name?')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mykeysid'), ('handleType', 'keyset'))),
            call.create_request().close(properties=[('reason', 'INVALID_HANDLE')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_keyset_by_handle(u'mykeysid')])

    def test_keyset(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact()
        WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        WHOIS.get_keyset_by_handle.return_value = self._get_keyset()
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_keyset", kwargs={"handle": "mykeysid"}))
        self.assertContains(response, "Key set details")
        self.assertContains(response, "Search results for handle <strong>mykeysid</strong>:")
        dns_key = 'DNS Key Flags: 257 (ZONE, Secure Entry Point (SEP)) Protocol: 3 (DNSSEC) Algorithm: 5 (RSA/SHA-1) ' \
                  'Key: AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxW EA4RJ9Ao6LCWheg8'
        self.assertCssSelectEqual(response, "table.result tr", [
            'Key set KEYSID-1',
            dns_key,
            'Technical contact KONTAKT Company L.t.d.',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mykeysid'), ('handleType', 'keyset'))),
            call.create_request().close(properties=[('foundType', 'keyset')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_keyset_by_handle('mykeysid'),
            call.get_keyset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_append_keyset_related(self):
        keyset = self._get_keyset()
        admin = self._get_contact()
        registrar = self._get_registrar()
        WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        WHOIS.get_contact_by_handle.return_value = admin
        WHOIS.get_registrar_by_handle.return_value = registrar
        data = {"detail": keyset}
        KeysetDetailMixin.append_keyset_related(data)
        self.assertEqual(data, {
            "detail": keyset,
            "admins": [admin],
            "registrar": registrar,
            "status_descriptions": ['Has relation to other records in the registry'],
        })

    def test_keyset_with_contact_no_organization(self):
        "Test for set disclose of organization to True."
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(
            organization=DisclosableString(value='', disclose=True))
        WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        WHOIS.get_keyset_by_handle.return_value = self._get_keyset()
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_keyset", kwargs={"handle": "mykeysid"}))
        self.assertContains(response, "Key set details")
        self.assertContains(response, "Search results for handle <strong>mykeysid</strong>:")
        dns_key = 'DNS Key Flags: 257 (ZONE, Secure Entry Point (SEP)) Protocol: 3 (DNSSEC) Algorithm: 5 (RSA/SHA-1) ' \
                  'Key: AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxW EA4RJ9Ao6LCWheg8'
        self.assertCssSelectEqual(response, "table.result tr", [
            'Key set KEYSID-1',
            dns_key,
            'Technical contact KONTAKT Arnold Rimmer',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'mykeysid'), ('handleType', 'keyset'))),
            call.create_request().close(properties=[('foundType', 'keyset')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_keyset_by_handle('mykeysid'),
            call.get_keyset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])


@override_settings(TEMPLATES=TEMPLATES)
class TestDetailDomain(ObjectDetailMixin):

    def test_domain_not_found(self):
        WHOIS.get_domain_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_managed_zone_list.return_value = ['cz', '0.2.4.e164.arpa']
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.cz"}))
        self.assertContains(response, 'Domain not found')
        self.assertContains(response, 'No domain matches <strong>fred.cz</strong> handle.')
        self.assertContains(response, 'Register this domain name?')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'fred.cz'), ('handleType', 'domain'))),
            call.create_request().close(properties=[])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_domain_by_handle('fred.cz')])

    def test_domain_not_found_idna_formated(self):
        WHOIS.get_domain_by_handle.side_effect = OBJECT_NOT_FOUND
        WHOIS.get_managed_zone_list.return_value = ['cz', '0.2.4.e164.arpa']
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "...fred.cz"}))
        self.assertContains(response, 'Invalid handle')
        self.assertContains(response, '<strong>...fred.cz</strong> is not a valid handle.')
        self.assertNotContains(response, 'Register this domain name?')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', '...fred.cz'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('reason', 'INVALID_HANDLE')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [])

    def _mocks_for_domain_detail(self, handle=None):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact()
        WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        WHOIS.get_keyset_by_handle.return_value = self._get_keyset()
        WHOIS.get_domain_status_descriptions.return_value = self._get_domain_status()
        WHOIS.get_domain_by_handle.return_value = self._get_domain(handle=handle) if handle else self._get_domain()
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()

    @patch("webwhois.views.detail_domain.WEBWHOIS_DNSSEC_URL", WEBWHOIS_DNSSEC_URL)
    def test_domain(self):
        self._mocks_for_domain_detail()
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.cz"}))
        self.assertContains(response, "Domain name details")
        self.assertContains(response, "Search results for handle <strong>fred.cz</strong>:")
        dns_key = 'DNS Key Flags: 257 (ZONE, Secure Entry Point (SEP)) Protocol: 3 (DNSSEC) Algorithm: 5 (RSA/SHA-1) ' \
                  'Key: AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxW EA4RJ9Ao6LCWheg8'
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
            dns_key,
            'Technical contact KONTAKT Company L.t.d.',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'fred.cz'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('foundType', 'domain')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_domain_by_handle('fred.cz'),
            call.get_domain_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_nsset_by_handle('NSSET-1'),
            call.get_nsset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_keyset_by_handle('KEYSID-1'),
            call.get_keyset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])
        self.assertContains(response, '<a href="%s">DNSSEC</a>' % WEBWHOIS_DNSSEC_URL, html=True)

    def test_domain_with_contact_no_organization(self):
        "Test for set disclose of organization to True."
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(
            organization=DisclosableString(value='', disclose=True))
        WHOIS.get_nsset_status_descriptions.return_value = self._get_nsset_status()
        WHOIS.get_nsset_by_handle.return_value = self._get_nsset()
        WHOIS.get_keyset_status_descriptions.return_value = self._get_keyset_status()
        WHOIS.get_keyset_by_handle.return_value = self._get_keyset()
        WHOIS.get_domain_status_descriptions.return_value = self._get_domain_status()
        WHOIS.get_domain_by_handle.return_value = self._get_domain()
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.cz"}))
        self.assertContains(response, "Domain name details")
        self.assertContains(response, "Search results for handle <strong>fred.cz</strong>:")
        dns_key = 'DNS Key Flags: 257 (ZONE, Secure Entry Point (SEP)) Protocol: 3 (DNSSEC) Algorithm: 5 (RSA/SHA-1) ' \
                  'Key: AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxW EA4RJ9Ao6LCWheg8'
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
            dns_key,
            'Technical contact KONTAKT Arnold Rimmer',
            'Sponsoring registrar REG-FRED_A Company A L.t.d. since Dec. 11, 2015, 7:18 p.m.',
            'Status Has relation to other records in the registry'
        ], transform=self.transform_to_text)
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'fred.cz'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('foundType', 'domain')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_domain_by_handle('fred.cz'),
            call.get_domain_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_nsset_by_handle('NSSET-1'),
            call.get_nsset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_keyset_by_handle('KEYSID-1'),
            call.get_keyset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_domain_without_nsset_and_keyset(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact()
        WHOIS.get_domain_status_descriptions.return_value = self._get_domain_status()
        WHOIS.get_domain_by_handle.return_value = self._get_domain(nsset_handle=None, keyset_handle=None)
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
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
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'fred.cz'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('foundType', 'domain')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_domain_by_handle('fred.cz'),
            call.get_domain_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_contact_by_handle('KONTAKT')
        ])

    def test_domain_unmanaged_zone(self):
        WHOIS.get_domain_by_handle.side_effect = UNMANAGED_ZONE
        WHOIS.get_managed_zone_list.return_value = ['cz', '0.2.4.e164.arpa']
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.com"}))
        self.assertContains(response, 'Unmanaged zone')
        msg = 'Domain <strong>fred.com</strong> cannot be found in the registry. ' \
              'You can search for domains in the these zones only:'
        self.assertContains(response, msg)
        self.assertNotContains(response, 'Register this domain name?')
        self.assertCssSelectEqual(response, "ul li", ['cz', '0.2.4.e164.arpa'], transform=self.transform_to_text)
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'fred.com'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('reason', 'UNMANAGED_ZONE')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_domain_by_handle('fred.com'), call.get_managed_zone_list()])

    def test_domain_idna_invalid_codepoint(self):
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fr:ed.com"}))
        self.assertContains(response, 'Invalid handle')
        self.assertContains(response, '<strong>fr:ed.com</strong> is not a valid handle.')
        self.assertNotContains(response, 'Register this domain name?')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'fr:ed.com'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('reason', 'IDNAError')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [])

    def test_domain_invalid_label(self):
        WHOIS.get_domain_by_handle.side_effect = INVALID_LABEL
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.com"}))
        self.assertContains(response, 'Invalid handle')
        self.assertContains(response, '<strong>fred.com</strong> is not a valid handle.')
        self.assertNotContains(response, 'Register this domain name?')

    def test_domain_invalid_label_with_dash(self):
        WHOIS.get_domain_by_handle.side_effect = INVALID_LABEL
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "-abc"}))
        self.assertContains(response, 'Invalid handle')
        self.assertContains(response, '<strong>-abc</strong> is not a valid handle.')
        self.assertNotContains(response, 'Register this domain name?')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', '-abc'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('reason', 'IDNAError')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [])

    def test_domain_too_many_labels(self):
        WHOIS.get_domain_by_handle.side_effect = TOO_MANY_LABELS
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "www.fred.cz"}))
        self.assertContains(response, "Incorrect input")
        self.assertContains(response, "Too many parts in the domain name <strong>www.fred.cz</strong>.")
        self.assertContains(response, "Enter only the name and the zone:")
        self.assertXpathEqual(response, "//a[text()='fred.cz']/@href",
                              [reverse("webwhois:form_whois") + "?handle=fred.cz"])
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'www.fred.cz'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('reason', 'TOO_MANY_LABELS')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_domain_by_handle('www.fred.cz')])

    def test_domain_too_many_labels_with_dot_at_the_end(self):
        WHOIS.get_domain_by_handle.side_effect = TOO_MANY_LABELS
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "www.fred.cz."}))
        self.assertContains(response, "Incorrect input")
        self.assertContains(response, "Too many parts in the domain name <strong>www.fred.cz.</strong>.")
        self.assertContains(response, "Enter only the name and the zone:")
        self.assertXpathEqual(response, "//a[text()='fred.cz']/@href",
                              [reverse("webwhois:form_whois") + "?handle=fred.cz"])
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'www.fred.cz.'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('reason', 'TOO_MANY_LABELS')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_domain_by_handle('www.fred.cz.')])

    def test_idn_domain(self):
        self._mocks_for_domain_detail(handle="xn--frd-cma.cz")
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": u"fréd.cz"}))
        self.assertContains(response, u"Search results for handle <strong>fréd.cz</strong>:")
        self.assertCssSelectEqual(response, ".domain .handle", ["xn--frd-cma.cz"], transform=self.transform_to_text)
        self.assertCssSelectEqual(response, ".domain .idn-handle", [u"fréd.cz"], transform=self.transform_to_text)
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', u'fréd.cz'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('foundType', 'domain')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_domain_by_handle('xn--frd-cma.cz'),
            call.get_domain_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_nsset_by_handle('NSSET-1'),
            call.get_nsset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_keyset_by_handle('KEYSID-1'),
            call.get_keyset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_idn_domain_punycode(self):
        self._mocks_for_domain_detail(handle="xn--frd-cma.cz")
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "xn--frd-cma.cz"}))
        self.assertContains(response, "Search results for handle <strong>xn--frd-cma.cz</strong>:")
        self.assertCssSelectEqual(response, ".domain .handle", ["xn--frd-cma.cz"], transform=self.transform_to_text)
        self.assertCssSelectEqual(response, ".domain .idn-handle", [u"fréd.cz"], transform=self.transform_to_text)
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'xn--frd-cma.cz'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('foundType', 'domain')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [
            call.get_domain_by_handle('xn--frd-cma.cz'),
            call.get_domain_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_nsset_by_handle('NSSET-1'),
            call.get_nsset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_keyset_by_handle('KEYSID-1'),
            call.get_keyset_status_descriptions('en'),
            call.get_contact_by_handle('KONTAKT'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])

    def test_domain_with_datetime_zero_values(self):
        date = DateType(day=0, month=0, year=0)
        datetime = DateTimeType(date=date, hour=0, minute=0, second=0),
        WHOIS.get_domain_by_handle.return_value = self._get_domain(
            handle='fred.cz',
            registrant_handle='',
            admin_contact_handles=[],
            nsset_handle=None,
            keyset_handle=None,
            registrar_handle='',
            statuses=[STATUS_DELETE_CANDIDATE],
            registered=datetime,
            changed=None,
            last_transfer=None,
            expire=date,
            expire_time_estimate=datetime,
            expire_time_actual=None,
            validated_to=None,
            validated_to_time_estimate=None,
            validated_to_time_actual=None
        )
        WHOIS.get_domain_status_descriptions.return_value = self._get_domain_status()
        response = self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.cz"}))
        self.assertCssSelectEqual(response, ".domain tr td", ["fred.cz", "To be deleted"],
                                  transform=self.transform_to_text)
        self.assertEqual(WHOIS.mock_calls, [
            call.get_domain_by_handle('fred.cz'),
            call.get_domain_status_descriptions('en')
        ])
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'fred.cz'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('foundType', 'domain')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')

    def test_unexpected_exeption(self):
        class TestException(Exception):
            pass
        WHOIS.get_domain_by_handle.side_effect = TestException("Unexpected exception.")
        with self.assertRaises(TestException):
            self.client.get(reverse("webwhois:detail_domain", kwargs={"handle": "fred.cz"}))
        self.assertEqual(WHOIS.mock_calls, [call.get_domain_by_handle('fred.cz')])
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'fred.cz'), ('handleType', 'domain'))),
            call.create_request().close(properties=[('exception', 'TestException')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Error')


@override_settings(USE_TZ=True, TIME_ZONE='Europe/Prague', FORMAT_MODULE_PATH=None, LANGUAGE_CODE='en',
                   CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}},
                   ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestContactDetailWithMojeid(WebwhoisAssertMixin, GetRegistryObjectMixin, SimpleTestCase):

    def setUp(self):
        spec = ('get_contact_by_handle', 'get_contact_status_descriptions', 'get_registrar_by_handle')
        apply_patch(self, patch.object(WHOIS, 'client', spec=spec))
        self.LOGGER = apply_patch(self, patch("webwhois.views.base.LOGGER"))
        self.LOGGER.__nonzero__.return_value = False

    @patch("webwhois.views.detail_contact.WEBWHOIS_MOJEID_TRANSFER_ENDPOINT", WEBWHOIS_MOJEID_TRANSFER_ENDPOINT)
    @patch("webwhois.views.detail_contact.WEBWHOIS_MOJEID_REGISTRY_ENDPOINT", WEBWHOIS_MOJEID_REGISTRY_ENDPOINT)
    @patch("webwhois.views.detail_contact.WEBWHOIS_MOJEID_LINK_WHY", WEBWHOIS_MOJEID_LINK_WHY)
    def test_button_mojeid(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact()
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_mojeid_contact", kwargs={"handle": "mycontact"}))
        self.assertXpathEqual(response, "//form[@action='%s']/input" % WEBWHOIS_MOJEID_TRANSFER_ENDPOINT, [
            ('hidden', 'username', 'kontakt'),
            ('submit', None, 'Create mojeID from the domain registry')
        ], transform=lambda node: (node.attrib["type"], node.attrib.get("name"), node.attrib["value"]), normalize=False)
        self.assertXpathEqual(response, "count(//a[@href='%s?username=kontakt'])=1" % (
            WEBWHOIS_MOJEID_REGISTRY_ENDPOINT), True)
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % WEBWHOIS_MOJEID_LINK_WHY, ["Why mojeID?"])
        self.assertEqual(self.LOGGER.mock_calls, [call.__nonzero__()])
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('mycontact'),
            call.get_contact_status_descriptions('en'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % WEBWHOIS_MOJEID_LINK_WHY, ["Why mojeID?"])

    @patch("webwhois.views.detail_contact.WEBWHOIS_MOJEID_TRANSFER_ENDPOINT", None)
    @patch("webwhois.views.detail_contact.WEBWHOIS_MOJEID_REGISTRY_ENDPOINT", None)
    @patch("webwhois.views.detail_contact.WEBWHOIS_MOJEID_LINK_WHY", None)
    def test_no_button_mojeid(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact()
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_mojeid_contact", kwargs={"handle": "mycontact"}))
        self.assertXpathEqual(response, "//form[@action='%s']/input" % WEBWHOIS_MOJEID_TRANSFER_ENDPOINT, [])
        self.assertXpathEqual(response, "count(//a[@href='%s?username=kontakt'])=1" % (
            WEBWHOIS_MOJEID_REGISTRY_ENDPOINT), False)
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % WEBWHOIS_MOJEID_LINK_WHY, [])
        # TODO: LOGGER, WHOIS

    def test_improper_handle_format(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(handle="MY.HANDLE")
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_mojeid_contact", kwargs={"handle": "MY.HANDLE"}))
        self.assertXpathEqual(response, "count(//form)=0", True)
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % WEBWHOIS_MOJEID_LINK_WHY, [])
        self.assertEqual(self.LOGGER.mock_calls, [call.__nonzero__()])
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('MY.HANDLE'),
            call.get_contact_status_descriptions('en'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % WEBWHOIS_MOJEID_LINK_WHY, [])

    @patch("webwhois.views.detail_contact.WEBWHOIS_MOJEID_TRANSFER_ENDPOINT", WEBWHOIS_MOJEID_TRANSFER_ENDPOINT)
    @patch("webwhois.views.detail_contact.WEBWHOIS_MOJEID_REGISTRY_ENDPOINT", WEBWHOIS_MOJEID_REGISTRY_ENDPOINT)
    @patch("webwhois.views.detail_contact.WEBWHOIS_MOJEID_LINK_WHY", WEBWHOIS_MOJEID_LINK_WHY)
    def test_status_not_linked(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=[])
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_mojeid_contact", kwargs={"handle": "mycontact"}))
        self.assertXpathEqual(response, "//form[@action='%s']/input" % WEBWHOIS_MOJEID_TRANSFER_ENDPOINT, [
            ('hidden', 'username', 'kontakt'),
            ('submit', None, 'Create mojeID from the domain registry')
        ], transform=lambda node: (node.attrib["type"], node.attrib.get("name"), node.attrib["value"]), normalize=False)
        self.assertXpathEqual(response, "count(//a[@href='%s?username=kontakt'])=1" % (
            WEBWHOIS_MOJEID_REGISTRY_ENDPOINT), True)
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % WEBWHOIS_MOJEID_LINK_WHY, ["Why mojeID?"])
        self.assertEqual(self.LOGGER.mock_calls, [call.__nonzero__()])
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('mycontact'),
            call.get_contact_status_descriptions('en'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % WEBWHOIS_MOJEID_LINK_WHY, ["Why mojeID?"])

    @patch("webwhois.views.detail_contact.WEBWHOIS_MOJEID_TRANSFER_ENDPOINT", None)
    @patch("webwhois.views.detail_contact.WEBWHOIS_MOJEID_REGISTRY_ENDPOINT", None)
    @patch("webwhois.views.detail_contact.WEBWHOIS_MOJEID_LINK_WHY", None)
    def test_status_not_linked_without_mojeid_form(self):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=[])
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_mojeid_contact", kwargs={"handle": "mycontact"}))
        self.assertXpathEqual(response, "//form[@action='%s']/input" % WEBWHOIS_MOJEID_TRANSFER_ENDPOINT, [])
        self.assertXpathEqual(response, "count(//a[@href='%s?username=kontakt'])=1" % (
            WEBWHOIS_MOJEID_REGISTRY_ENDPOINT), False)
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % WEBWHOIS_MOJEID_LINK_WHY, [])
        # TODO: LOGGER, WHOIS

    def _do_test_statuses(self, statuses):
        WHOIS.get_contact_status_descriptions.return_value = self._get_contact_status()
        WHOIS.get_contact_by_handle.return_value = self._get_contact(statuses=statuses)
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_mojeid_contact", kwargs={"handle": "mycontact"}))
        self.assertXpathEqual(response, "count(//form)=0", True)
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % WEBWHOIS_MOJEID_LINK_WHY, [])
        self.assertEqual(self.LOGGER.mock_calls, [call.__nonzero__()])
        self.assertEqual(WHOIS.mock_calls, [
            call.get_contact_by_handle('mycontact'),
            call.get_contact_status_descriptions('en'),
            call.get_registrar_by_handle('REG-FRED_A'),
            call.get_registrar_by_handle('REG-FRED_A')
        ])
        self.assertXpathEqual(response, "//a[@href='%s']/text()" % WEBWHOIS_MOJEID_LINK_WHY, [])

    def test_status_mojeid_contact(self):
        self._do_test_statuses([STATUS_LINKED, STATUS_MOJEID_CONTACT])

    def test_status_server_transfer_prohibited(self):
        self._do_test_statuses([STATUS_LINKED, STATUS_TRANSFER_PROHIBITED])

    def test_status_server_update_prohibited(self):
        self._do_test_statuses([STATUS_LINKED, STATUS_UPDATE_PROHIBITED])

    def test_status_server_delete_prohibited(self):
        self._do_test_statuses([STATUS_LINKED, STATUS_DELETE_PROHIBITED])

    def test_status_delete_candidate(self):
        self._do_test_statuses([STATUS_LINKED, STATUS_DELETE_CANDIDATE])

    def test_status_server_blocked(self):
        self._do_test_statuses([STATUS_LINKED, STATUS_SERVER_BLOCKED])


class FakeRegistryObjectView(RegistryObjectMixin, View):
    """Test view for RegistryObjectMixin."""

    _registry_objects_key = 'bollox'
    object_type_name = sentinel.type_name

    def __init__(self, object_mock):
        self.object_mock = object_mock

    def load_registry_object(self, context, handle):
        context[self._registry_objects_key] = {self.object_type_name: {'detail': self.object_mock}}


class TestRegistryObjectMixin(SimpleTestCase):
    """Test RegistryObjectMixin class."""

    def test_logging_request(self):
        view = RegistryObjectMixin()
        with self.assertRaises(NotImplementedError):
            view.prepare_logging_request()

    def test_context_is_not_delete_candidate(self):
        view = FakeRegistryObjectView(make_keyset(statuses=[]))
        view.kwargs = {'handle': sentinel.handle}
        with patch("webwhois.views.base.LOGGER", None):
            context = view.get_context_data(handle=sentinel.handle)
        self.assertFalse(context['object_delete_candidate'])

    def test_context_is_delete_candidate(self):
        view = FakeRegistryObjectView(make_keyset(statuses=[STATUS_DELETE_CANDIDATE]))
        view.kwargs = {'handle': sentinel.handle}
        with patch("webwhois.views.base.LOGGER", None):
            context = view.get_context_data(handle=sentinel.handle)
        self.assertTrue(context['object_delete_candidate'])
