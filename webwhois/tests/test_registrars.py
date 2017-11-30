#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

from django.http.response import HttpResponseNotFound
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils._os import upath
from fred_idl.ccReg import FileInfo
from fred_idl.Registry.Whois import INVALID_HANDLE, OBJECT_NOT_FOUND, Registrar, RegistrarCertification, RegistrarGroup
from mock import call, patch

from webwhois.tests.get_registry_objects import GetRegistryObjectMixin
from webwhois.tests.utils import TEMPLATES, WebwhoisAssertMixin, apply_patch
from webwhois.utils import FILE_MANAGER, WHOIS


@patch('webwhois.views.registrar.WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED', ['certified'])
@patch('webwhois.views.registrar.WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED', ['uncertified'])
@override_settings(ROOT_URLCONF='webwhois.tests.urls', STATIC_URL='/static/', TEMPLATES=TEMPLATES)
class TestRegistrarsView(WebwhoisAssertMixin, GetRegistryObjectMixin, SimpleTestCase):

    def setUp(self):
        spec = ('get_registrar_by_handle', 'get_registrar_certification_list', 'get_registrar_groups', 'get_registrars')
        apply_patch(self, patch.object(WHOIS, 'client', spec=spec))
        self.LOGGER = apply_patch(self, patch("webwhois.views.base.LOGGER"))

    def test_registrar_not_found(self):
        WHOIS.get_registrar_by_handle.side_effect = OBJECT_NOT_FOUND
        response = self.client.get(reverse("webwhois:detail_registrar", kwargs={"handle": "REG_FRED_A"}))
        self.assertContains(response, 'Registrar not found')
        self.assertContains(response, 'No registrar matches <strong>REG_FRED_A</strong> handle.')
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'REG_FRED_A'), ('handleType', 'registrar'))),
            call.create_request().close(properties=[])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_registrar_by_handle('REG_FRED_A')])

    def test_registrar_invalid_handle(self):
        WHOIS.get_registrar_by_handle.side_effect = INVALID_HANDLE
        response = self.client.get(reverse("webwhois:detail_registrar", kwargs={"handle": "REG_FRED_A"}))
        self.assertContains(response, "Invalid handle")
        self.assertContains(response, "<strong>REG_FRED_A</strong> is not a valid handle.")
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'REG_FRED_A'), ('handleType', 'registrar'))),
            call.create_request().close(properties=[('reason', 'INVALID_HANDLE')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'NotFound')
        self.assertEqual(WHOIS.mock_calls, [call.get_registrar_by_handle('REG_FRED_A')])

    def test_registrar(self):
        WHOIS.get_registrar_by_handle.return_value = self._get_registrar()
        response = self.client.get(reverse("webwhois:detail_registrar", kwargs={"handle": "REG_FRED_A"}))
        self.assertContains(response, "Registrar details")
        self.assertContains(response, "Search results for handle <strong>REG_FRED_A</strong>:")
        self.assertCssSelectEqual(response, "table.registrar tr", [
            'Handle REG-FRED_A',
            'Name Company A L.t.d.',
            'Phone +420.72645123',
            'Fax +420.72645124',
            'URL www.nic.cz',
            'Address The street 123, 12300 Prague, CZ'
        ], transform=self.transform_to_text)
        self.assertCssSelectEqual(response, ".url a", [
            ("http://www.nic.cz", "www.nic.cz")
        ], transform=lambda node: (node.attrib["href"], self.transform_to_text(node)), normalize=False)
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'REG_FRED_A'), ('handleType', 'registrar'))),
            call.create_request().close(properties=[('foundType', 'registrar')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [call.get_registrar_by_handle('REG_FRED_A')])

    def test_registrar_url_with_schema(self):
        registrar = self._get_registrar()
        registrar.url = "https://foo.foo"
        WHOIS.get_registrar_by_handle.return_value = registrar
        response = self.client.get(reverse("webwhois:detail_registrar", kwargs={"handle": "REG_FRED_A"}))
        self.assertCssSelectEqual(response, ".url a", [
            ("https://foo.foo", "foo.foo")
        ], transform=lambda node: (node.attrib["href"], self.transform_to_text(node)), normalize=False)
        self.assertEqual(self.LOGGER.mock_calls, [
            call.__nonzero__(),
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'REG_FRED_A'), ('handleType', 'registrar'))),
            call.create_request().close(properties=[('foundType', 'registrar')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [call.get_registrar_by_handle('REG_FRED_A')])

    def test_registrars_retail(self):
        WHOIS.get_registrar_groups.return_value = self._get_registrar_groups()
        WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        WHOIS.get_registrars.return_value = self._get_registrars()
        response = self.client.get(reverse("webwhois:registrar_list_retail"))
        self.assertContains(response, "Registrars offering also retail services")
        self.assertCssSelectEqual(response, "table.registrars tr", [
            'Registrar Website Technologies Certification Evaluation protocol',
            'MojeID s.r.o. www.mojeid.cz',
            'Company A L.t.d. www.fred-a.cz',
            'Company B L.t.d. www.fred-b.cz'
        ], transform=self.transform_to_text)

        # Technologies (number of icons):
        # MojeID registrar
        self.assertXpathEqual(response, "count(//table[contains(@class, 'registrars')]/tr[2]/td[3]//img)=0", True)
        # Testing registrar A
        self.assertXpathEqual(response, "//table[contains(@class, 'registrars')]/tr[3]/td[3]//img/@src", [
            "/static/webwhois/img/technology/dnssec.png",
            "/static/webwhois/img/technology/mojeid.png",
        ], transform=lambda node: node)
        # Testing registrar B
        self.assertXpathEqual(response, "//table[contains(@class, 'registrars')]/tr[4]/td[3]//img/@src", [
            "/static/webwhois/img/technology/ipv6.png",
        ], transform=lambda node: node)

        # Certification (number of stars):
        # MojeID registrar
        self.assertXpathEqual(response, "count(//table[contains(@class, 'registrars')]/tr[2]/td[4]//img)=8", True)
        # Testing registrar A
        self.assertXpathEqual(response, "count(//table[contains(@class, 'registrars')]/tr[3]/td[4]//img)=2", True)
        # Testing registrar B
        self.assertXpathEqual(response, "count(//table[contains(@class, 'registrars')]/tr[4]/td[4]//img)=0", True)

        # Evaluation protocol (links):
        self.assertXpathEqual(response, "//table[contains(@class, 'registrars')]/tr/td[5]//a/@href", [
            '/whois/registrar-download-evaluation-file/REG-MOJEID/',
            '/whois/registrar-download-evaluation-file/REG-FRED_A/',
        ], transform=lambda node: node)

        self.assertXpathEqual(response, "//*[contains(@class, 'registrars')]//a/@href", [
            'http://www.mojeid.cz', '/whois/registrar-download-evaluation-file/REG-MOJEID/',
            'http://www.fred-a.cz', '/whois/registrar-download-evaluation-file/REG-FRED_A/',
            'http://www.fred-b.cz'
        ])
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars()
        ])

    def test_registrars_wholesale(self):
        WHOIS.get_registrar_groups.return_value = self._get_registrar_groups()
        WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        WHOIS.get_registrars.return_value = self._get_registrars()
        response = self.client.get(reverse("webwhois:registrar_list_wholesale"))
        self.assertContains(response, "Registrars offering only wholesale services")
        self.assertCssSelectEqual(response, "table.registrars tr", [
            'Registrar Website Technologies',
            'Company C L.t.d. www.no-credit.cz',
        ], transform=self.transform_to_text)
        self.assertXpathEqual(response, "//*[contains(@class, 'registrars')]//a/@href", ["https://www.no-credit.cz"])
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars()
        ])

    def test_dobradomena_list_retail(self):
        WHOIS.get_registrar_groups.return_value = self._get_registrar_groups()
        WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        WHOIS.get_registrars.return_value = self._get_registrars()
        response = self.client.get(reverse("webwhois:dobradomena_list_retail"))
        self.assertContains(response, "Registrars offering also retail services")
        self.assertCssSelectEqual(response, "div:not(:first-child)", [
            'Registrar supports secured domains DNSSEC',
            'Registrar supports mojeID',
            'Registrar supports IPv6',
            'Registrar Certified for Retail',
        ], transform=self.transform_to_text)
        self.assertXpathEqual(response, "//table[contains(@class, 'registrars')]/tr[1]/th[6]", [
            u'How to register a Dobrá doména.'
        ], transform=self.transform_to_text)

        # How to register "Dobrá doména":
        # MojeID registrar
        self.assertXpathEqual(response, "count(//table[contains(@class, 'registrars')]/tr[2]/td[6]/a)=0", True)
        # Testing registrar A
        self.assertXpathEqual(response, "//table[contains(@class, 'registrars')]/tr[3]/td[6]/a/@href", [
            'http://fred-a.dobradomena.cz/manual.pdf',
        ], transform=lambda node: node)
        # Testing registrar B
        self.assertXpathEqual(response, "//table[contains(@class, 'registrars')]/tr[4]/td[6]/a/@href", [
            'http://fred-b.dobradomena.cz/manual.pdf',
        ], transform=lambda node: node)
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars()
        ])

    def _table_line(self, node):
        regisrar_name = self.normalize_spaces("".join(node.xpath("td[1]/text()")))
        stars = "*" * int(node.xpath("count(td[4]//img)"))
        return (regisrar_name, stars)

    @patch("webwhois.views.registrar.random.SystemRandom.shuffle")
    def test_shuffle_and_sorted_registrars(self, mock_shuffle):
        WHOIS.get_registrar_groups.return_value = self._get_registrar_groups()
        WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        WHOIS.get_registrars.return_value = self._get_registrars()
        WHOIS.get_registrar_groups.return_value[0].members.extend(("REG-ACTIVE", "REG-DEACTIVE", "REG-FRED_X",
                                                                   "REG-FRED_Y"))
        WHOIS.get_registrar_certification_list.return_value.extend((
            RegistrarCertification(registrar_handle='REG-ACTIVE', score=8, evaluation_file_id=None),
            RegistrarCertification(registrar_handle='REG-DEACTIVE', score=8, evaluation_file_id=None),
            RegistrarCertification(registrar_handle='REG-FRED_X', score=2, evaluation_file_id=None),
            RegistrarCertification(registrar_handle='REG-FRED_Y', score=2, evaluation_file_id=None),
        ))
        WHOIS.get_registrars.return_value.extend((
            Registrar(
                handle='REG-FRED_X', name="Company X L.t.d.", organization='Testing registrar X', url='www.fred-x.cz',
                phone='', fax='', address=self._get_place_address()),
            Registrar(
                handle='REG-FRED_Y', name="Company Y L.t.d.", organization='Testing registrar Y', url='www.fred-y.cz',
                phone='', fax='', address=self._get_place_address()),
            Registrar(
                handle='REG-ACTIVE', name="Active L.t.d.", organization='Active registrar', url='www.active.cz',
                phone='', fax='', address=self._get_place_address()),
            Registrar(
                handle='REG-DEACTIVE', name="Deactive L.t.d.", organization='Deactive registrar', url='www.deactive.cz',
                phone='', fax='', address=self._get_place_address()),
        ))

        mock_shuffle.side_effect = lambda regs: regs.sort(key=lambda row: row['registrar'].name, reverse=False)
        response = self.client.get(reverse("webwhois:registrar_list_retail"))

        self.assertXpathEqual(response, "//table[contains(@class, 'registrars')]//tr[position()>1]", [
            ('Active L.t.d.',    '********'),
            ('Deactive L.t.d.',  '********'),
            ('MojeID s.r.o.',    '********'),
            ('Company A L.t.d.', '**'),
            ('Company X L.t.d.', '**'),
            ('Company Y L.t.d.', '**'),
            ('Company B L.t.d.', ''),
        ], transform=self._table_line, normalize=False)

        mock_shuffle.side_effect = lambda regs: regs.sort(key=lambda row: row['registrar'].name, reverse=True)
        response = self.client.get(reverse("webwhois:registrar_list_retail"))
        self.assertXpathEqual(response, "//table[contains(@class, 'registrars')]//tr[position()>1]", [
            ('MojeID s.r.o.',    '********'),
            ('Deactive L.t.d.',  '********'),
            ('Active L.t.d.',    '********'),
            ('Company Y L.t.d.', '**'),
            ('Company X L.t.d.', '**'),
            ('Company A L.t.d.', '**'),
            ('Company B L.t.d.', '')
        ], transform=self._table_line, normalize=False)

        self.assertEqual(mock_shuffle.call_count, 2)
        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars(),
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars()
        ])


class SetMocksMixin(object):

    def setUp(self):
        spec = ('get_registrar_certification_list', 'get_registrar_groups', 'get_registrars')
        apply_patch(self, patch.object(WHOIS, 'client', spec=spec))
        WHOIS.get_registrar_groups.return_value = self._get_registrar_groups() + [
            RegistrarGroup(name='foo', members=['REG-FOO'])
        ]
        WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        WHOIS.get_registrars.return_value = self._get_registrars() + [
            Registrar(
                handle='REG-FOO', name="Foo s.r.o.", organization='Foo registrar', url='www.foo.foo', phone='', fax='',
                address=self._get_place_address()),
        ]


@patch('webwhois.views.registrar.WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED', ['foo'])
@patch('webwhois.views.registrar.WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED', ['unfoo'])
@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestRegistrarsUnknownGroupNames(WebwhoisAssertMixin, SetMocksMixin, GetRegistryObjectMixin, SimpleTestCase):

    def test_registrars_retail(self):
        response = self.client.get(reverse("webwhois:registrar_list_retail"))
        self.assertContains(response, "Registrars offering also retail services")
        self.assertCssSelectEqual(response, "table.registrars tr", [
            'Registrar Website Technologies Certification Evaluation protocol',
            'Foo s.r.o. www.foo.foo'], transform=self.transform_to_text)
        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars()
        ])

    def test_registrars_wholesale(self):
        response = self.client.get(reverse("webwhois:registrar_list_wholesale"))
        self.assertContains(response, "Registrars offering only wholesale services")
        self.assertCssSelectEqual(response, "table.registrars tr", [
            'Registrar Website Technologies'], transform=self.transform_to_text)
        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars()
        ])


@patch('webwhois.views.registrar.WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED', [])
@patch('webwhois.views.registrar.WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED', [])
@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestRegistrarsEmptyGroupNames(WebwhoisAssertMixin, SetMocksMixin, GetRegistryObjectMixin, SimpleTestCase):

    def test_registrars_retail(self):
        response = self.client.get(reverse("webwhois:registrar_list_retail"))
        self.assertContains(response, "Registrars offering also retail services")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Registrar Website Technologies Certification Evaluation protocol'], transform=self.transform_to_text)
        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars()
        ])

    def test_registrars_wholesale(self):
        response = self.client.get(reverse("webwhois:registrar_list_wholesale"))
        self.assertContains(response, "Registrars offering only wholesale services")
        self.assertCssSelectEqual(response, "table.result tr", [
            'Registrar Website Technologies'], transform=self.transform_to_text)
        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars()
        ])


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(upath(__file__)), 'templates')],
    },
]


@override_settings(TEMPLATES=TEMPLATES, ROOT_URLCONF='webwhois.tests.urls')
class TestDownloadView(GetRegistryObjectMixin, SimpleTestCase):

    def setUp(self):
        apply_patch(self, patch.object(WHOIS, 'client', spec=('get_registrar_certification_list', )))
        apply_patch(self, patch.object(FILE_MANAGER, 'client', spec=('info', 'load')))

    def test_download_not_found(self):
        WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        response = self.client.get(reverse("webwhois:download_evaluation_file", kwargs={"handle": "REG-MISSING"}))
        self.assertIsInstance(response, HttpResponseNotFound)
        self.assertEqual(WHOIS.mock_calls, [call.get_registrar_certification_list()])
        self.assertEqual(FILE_MANAGER.mock_calls, [])

    def test_download_eval_file(self):
        WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        FILE_MANAGER.info.return_value = FileInfo(
            id=2,
            name='test.html',
            path='2015/12/9/1',
            mimetype='text/html',
            filetype=6,
            crdate='2015-12-09 16:16:28.598757',
            size=5L
        )
        content = "<html><body>The content.</body></html>"
        FILE_MANAGER.load.return_value.download.return_value = content
        response = self.client.get(reverse("webwhois:download_evaluation_file", kwargs={"handle": "REG-MOJEID"}))
        self.assertEqual(response.content, content)
        self.assertEqual(response['Content-Type'], 'text/html')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="test.html"')
        self.assertEqual(WHOIS.mock_calls, [call.get_registrar_certification_list()])
        self.assertEqual(FILE_MANAGER.mock_calls, [
            call.info(2L),
            call.load(2),
            call.load().download(5L),
            call.load().finalize_download()
        ])
