#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

from django.core.urlresolvers import reverse
from django.http.response import HttpResponseNotFound
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.utils._os import upath
from mock import patch

from webwhois.tests.get_registry_objects import GetRegistryObjectMixin
from webwhois.tests.utils import CorbaInitMixin, WebwhoisAssertMixin, apply_patch
from webwhois.utils import WHOIS_MODULE


class TestRegisrarsView(WebwhoisAssertMixin, CorbaInitMixin, GetRegistryObjectMixin, SimpleTestCase):

    urls = 'webwhois.tests.urls'

    def setUp(self):
        apply_patch(self, patch("webwhois.views.pages.CORBA", self.CORBA))
        self.WHOIS = apply_patch(self, patch("webwhois.views.pages.WHOIS"))
        self.RegWhois = WHOIS_MODULE

    def test_registrar_not_found(self):
        self.WHOIS.get_registrar_by_handle.side_effect = WHOIS_MODULE.OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:detail_registrar", kwargs={"handle": "REG_FRED_A"}))
        self.assertContains(response, 'Registrar not found')
        self.assertContains(response, 'No registrar matches <strong>REG_FRED_A</strong> handle.')

    def test_registrar_invalid_handle(self):
        self.WHOIS.get_registrar_by_handle.side_effect = WHOIS_MODULE.INVALID_HANDLE
        response = self.client.get(reverse("webwhois:detail_registrar", kwargs={"handle": "REG_FRED_A"}))
        self.assertContains(response, "Invalid handle")
        self.assertContains(response, "<strong>REG_FRED_A</strong> is not a valid handle.")

    def test_registrar(self):
        self.WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_registrar", kwargs={"handle": "REG_FRED_A"}))
        self.assertContains(response, "Registrar details")
        self.assertContains(response, "Search results for handle <strong>REG_FRED_A</strong>:")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Handle REG-FRED_A',
            'Name Company A L.t.d.',
            'Phone +420.72645123',
            'Fax +420.72645124',
            'URL www.nic.cz',
            'Address The street 123, 12300 Prague, CZ'
        ], transform=self.transform_to_text)

    def test_registrars_retail(self):
        self.WHOIS.get_registrar_groups.return_value = self._get_registrar_groups()
        self.WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        self.WHOIS.get_registrars.return_value = self._get_registrars()
        response = self.client.get(reverse("webwhois:registrar_list_retail"))
        self.assertContains(response, "Registrars offering also retail services")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Registrar Website Technologies Certification Evaluation protocol',
            'MojeID s.r.o. www.mojeid.cz',
            'Company A L.t.d. www.fred-a.cz',
            'Company B L.t.d. www.fred-b.cz'
        ], transform=self.transform_to_text)

        # Technologies (number of icons):
        # MojeID registrar
        self.assertXpathEqual(response, "count(//table[@class='result']/tr[2]/td[3]//img)=0", True)  # MojeID registrar
        # Testing registrar A
        self.assertXpathEqual(response, "//table[@class='result']/tr[3]/td[3]//img/@src", [
            "/static/webwhois/img/technology/dnssec.png",
            "/static/webwhois/img/technology/mojeid.png",
        ], transform=lambda node: node)
        # Testing registrar B
        self.assertXpathEqual(response, "//table[@class='result']/tr[4]/td[3]//img/@src", [
            "/static/webwhois/img/technology/ipv6.png",
        ], transform=lambda node: node)

        # Certification (number of stars):
        # MojeID registrar
        self.assertXpathEqual(response, "count(//table[@class='result']/tr[2]/td[4]//img)=8", True)
        # Testing registrar A
        self.assertXpathEqual(response, "count(//table[@class='result']/tr[3]/td[4]//img)=2", True)
        # Testing registrar B
        self.assertXpathEqual(response, "count(//table[@class='result']/tr[4]/td[4]//img)=0", True)

        # Evaluation protocol (links):
        self.assertXpathEqual(response, "//table[@class='result']/tr/td[5]//a/@href", [
            '/whois/registrar-download-evaluation-file/REG-MOJEID/',
            '/whois/registrar-download-evaluation-file/REG-FRED_A/',
        ], transform=lambda node: node)

        self.assertXpathEqual(response, "//*[@class='result']//a/@href", [
            'http://www.mojeid.cz', '/whois/registrar-download-evaluation-file/REG-MOJEID/',
            'http://www.fred-a.cz', '/whois/registrar-download-evaluation-file/REG-FRED_A/',
            'http://www.fred-b.cz'
        ])

    def test_registrars_wholesale(self):
        self.WHOIS.get_registrar_groups.return_value = self._get_registrar_groups()
        self.WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        self.WHOIS.get_registrars.return_value = self._get_registrars()
        response = self.client.get(reverse("webwhois:registrar_list_wholesale"))
        self.assertContains(response, "Registrars offering only wholesale services")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Registrar Website Technologies',
            'Company C L.t.d. www.no-credit.cz',
        ], transform=self.transform_to_text)
        self.assertXpathEqual(response, "//*[@class='result']//a/@href", ["https://www.no-credit.cz"])

    def test_dobradomena_list_retail(self):
        self.WHOIS.get_registrar_groups.return_value = self._get_registrar_groups()
        self.WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        self.WHOIS.get_registrars.return_value = self._get_registrars()
        response = self.client.get(reverse("webwhois:dobradomena_list_retail"))
        self.assertContains(response, "Registrars offering also retail services")
        self.assertCssSelectEqual(response, "div:not(:first-child)", [
            'Registrar supports secured domains DNSSEC',
            'Registrar supports mojeID',
            'Registrar supports IPv6',
            'Registrar Certified for Retail',
        ], transform=self.transform_to_text)
        self.assertXpathEqual(response, "//table[@class='result']/tr[1]/th[6]", [
            u'How to register a Dobrá doména.'
        ], transform=self.transform_to_text)

        # How to register "Dobrá doména":
        # MojeID registrar
        self.assertXpathEqual(response, "count(//table[@class='result']/tr[2]/td[6]/a)=0", True)
        # Testing registrar A
        self.assertXpathEqual(response, "//table[@class='result']/tr[3]/td[6]/a/@href", [
            'http://fred-a.dobradomena.cz/manual.pdf',
        ], transform=lambda node: node)
        # Testing registrar B
        self.assertXpathEqual(response, "//table[@class='result']/tr[4]/td[6]/a/@href", [
            'http://fred-b.dobradomena.cz/manual.pdf',
        ], transform=lambda node: node)


@override_settings(TEMPLATE_DIRS=(os.path.join(os.path.dirname(upath(__file__)), 'templates'), ))
class TestDownloadView(CorbaInitMixin, GetRegistryObjectMixin, SimpleTestCase):

    urls = 'webwhois.tests.urls'

    def setUp(self):
        apply_patch(self, patch("webwhois.views.pages.CORBA", self.CORBA))
        self.WHOIS = apply_patch(self, patch("webwhois.views.pages.WHOIS"))
        self.FILE = apply_patch(self, patch("webwhois.views.pages.FILEMANAGER"))
        self.RegWhois = WHOIS_MODULE

    def test_download_not_found(self):
        self.WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        response = self.client.get(reverse("webwhois:download_evaluation_file", kwargs={"handle": "REG-MISSING"}))
        self.assertIsInstance(response, HttpResponseNotFound)

    def test_download_eval_file(self):
        self.WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        self.FILE.info.return_value = self.CORBA.ccReg.FileInfo(
            id=2,
            name='test.html',
            path='2015/12/9/1',
            mimetype='text/html',
            filetype=6,
            crdate='2015-12-09 16:16:28.598757',
            size=5L
        )
        content = "<html><body>The content.</body></html>"
        self.FILE.load.return_value.download.return_value = content
        response = self.client.get(reverse("webwhois:download_evaluation_file", kwargs={"handle": "REG-MOJEID"}))
        self.assertEqual(response.content, content)
        self.assertEqual(response['Content-Type'], 'text/html')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="test.html"')
