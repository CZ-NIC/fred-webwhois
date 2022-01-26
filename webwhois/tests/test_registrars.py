#!/usr/bin/python
#
# Copyright (C) 2015-2021  CZ.NIC, z. s. p. o.
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
import os
import warnings
from unittest.mock import call, patch

from django.http.response import HttpResponseNotFound
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.urls import reverse
from fred_idl.ccReg import FileInfo
from fred_idl.Registry.Whois import INVALID_HANDLE, OBJECT_NOT_FOUND, RegistrarCertification, RegistrarGroup
from testfixtures import ShouldWarn

from webwhois.tests.get_registry_objects import GetRegistryObjectMixin
from webwhois.tests.utils import CALL_BOOL, TEMPLATES, apply_patch, make_registrar
from webwhois.utils import FILE_MANAGER, WHOIS


@override_settings(ROOT_URLCONF='webwhois.tests.urls', STATIC_URL='/static/', TEMPLATES=TEMPLATES)
class TestRegistrarsView(GetRegistryObjectMixin, SimpleTestCase):

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
            CALL_BOOL,
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
            CALL_BOOL,
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
        self.assertEqual(self.LOGGER.mock_calls, [
            CALL_BOOL,
            call.create_request('127.0.0.1', 'Web whois', 'Info', properties=(
                ('handle', 'REG_FRED_A'), ('handleType', 'registrar'))),
            call.create_request().close(properties=[('foundType', 'registrar')])
        ])
        self.assertEqual(self.LOGGER.create_request().result, 'Ok')
        self.assertEqual(WHOIS.mock_calls, [call.get_registrar_by_handle('REG_FRED_A')])


@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestRegistrarListView(SimpleTestCase):
    """Test RegistrarListView."""

    def setUp(self):
        spec = ('get_registrar_certification_list', 'get_registrar_groups', 'get_registrars')
        apply_patch(self, patch.object(WHOIS, 'client', spec=spec))

    def test_registrars_empty(self):
        WHOIS.get_registrars.return_value = []
        WHOIS.get_registrar_groups.return_value = []
        WHOIS.get_registrar_certification_list.return_value = []

        response = self.client.get(reverse('webwhois:registrars'))

        self.assertContains(response, "List of registrars")
        self.assertIsNone(response.context['is_retail'])
        self.assertEqual(len(response.context['registrars']), 0)
        self.assertEqual(WHOIS.mock_calls, [call.get_registrars(), call.get_registrar_groups()])

    def test_registrars(self):
        registrar = make_registrar()
        WHOIS.get_registrars.return_value = [registrar]
        WHOIS.get_registrar_groups.return_value = []
        WHOIS.get_registrar_certification_list.return_value = []

        response = self.client.get(reverse('webwhois:registrars'))

        self.assertContains(response, "List of registrars")
        self.assertIsNone(response.context['is_retail'])
        self.assertEqual(len(response.context['registrars']), 1)
        self.assertEqual(response.context['registrars'][0]['registrar'], registrar)
        self.assertEqual(WHOIS.mock_calls,
                         [call.get_registrars(), call.get_registrar_certification_list(), call.get_registrar_groups()])

    def test_registrars_certification_context(self):
        WHOIS.get_registrars.return_value = [make_registrar('HOLLY')]
        WHOIS.get_registrar_groups.return_value = []
        certification = RegistrarCertification('HOLLY', 3, None)
        WHOIS.get_registrar_certification_list.return_value = [certification]

        response = self.client.get(reverse('webwhois:registrars'))

        self.assertContains(response, "List of registrars")
        self.assertEqual(len(response.context['registrars']), 1)
        self.assertEqual(response.context['registrars'][0]['cert'], certification)
        self.assertEqual(response.context['registrars'][0]['score'], 3)
        self.assertEqual(response.context['registrars'][0]['stars'], range(3))
        self.assertEqual(WHOIS.mock_calls,
                         [call.get_registrars(), call.get_registrar_certification_list(), call.get_registrar_groups()])

    def test_registrars_group(self):
        WHOIS.get_registrars.return_value = [make_registrar(handle='HOLLY'), make_registrar(handle='GORDON')]
        WHOIS.get_registrar_groups.return_value = [RegistrarGroup(name='red_dwarf', members=['HOLLY'])]
        WHOIS.get_registrar_certification_list.return_value = []

        response = self.client.get(reverse('registrars_red_dwarf'))

        self.assertContains(response, "List of registrars")
        self.assertIsNone(response.context['is_retail'])
        self.assertEqual(len(response.context['registrars']), 1)
        self.assertEqual(response.context['registrars'][0]['registrar'].handle, 'HOLLY')
        self.assertEqual(WHOIS.mock_calls,
                         [call.get_registrars(), call.get_registrar_groups(), call.get_registrar_certification_list()])

    def test_registrars_group_unknown(self):
        # Test filter using the unknown group
        WHOIS.get_registrars.return_value = [make_registrar()]
        WHOIS.get_registrar_groups.return_value = []
        WHOIS.get_registrar_certification_list.return_value = []

        response = self.client.get(reverse('registrars_red_dwarf'))

        self.assertContains(response, "Not Found", status_code=404)
        self.assertEqual(WHOIS.mock_calls, [call.get_registrars(), call.get_registrar_groups()])

    def test_registrars_old_context(self):
        # Test deprecated `_registrar_row` works correctly
        registrar = make_registrar()
        WHOIS.get_registrars.return_value = [registrar]
        WHOIS.get_registrar_groups.return_value = []
        WHOIS.get_registrar_certification_list.return_value = []

        warn_msg = ("Method 'RegistrarListView._registrar_row' is deprecated in favor of "
                    "'RegistrarListView.get_registrar_context'.")
        with ShouldWarn(DeprecationWarning(warn_msg)):
            warnings.simplefilter('always')
            response = self.client.get(reverse('registrars_custom'))

        self.assertContains(response, "List of registrars")
        self.assertEqual(len(response.context['registrars']), 1)
        self.assertTrue(response.context['registrars'][0]['custom'])
        self.assertEqual(WHOIS.mock_calls,
                         [call.get_registrars(), call.get_registrar_certification_list(), call.get_registrar_groups()])

    def test_registrars_shuffle(self):
        holly = make_registrar(handle='HOLLY')
        queeg = make_registrar(handle='QUEEG')
        gordon = make_registrar(handle='GORDON')
        WHOIS.get_registrars.return_value = [holly, queeg, gordon]
        WHOIS.get_registrar_groups.return_value = []
        WHOIS.get_registrar_certification_list.return_value = []

        def _test_shuffle(registrars):
            registrars.sort(key=lambda row: row['registrar'].handle)

        with patch("webwhois.views.registrar.random.SystemRandom.shuffle", side_effect=_test_shuffle):
            response = self.client.get(reverse('webwhois:registrars'))

        self.assertContains(response, "List of registrars")
        self.assertEqual([r['registrar'] for r in response.context['registrars']], [gordon, holly, queeg])
        self.assertEqual(WHOIS.mock_calls,
                         [call.get_registrars(), call.get_registrar_certification_list(), call.get_registrar_groups()])

    def test_registrars_sorting(self):
        holly = make_registrar(handle='HOLLY')
        queeg = make_registrar(handle='QUEEG')
        gordon = make_registrar(handle='GORDON')
        WHOIS.get_registrars.return_value = [holly, queeg, gordon]
        WHOIS.get_registrar_groups.return_value = []
        WHOIS.get_registrar_certification_list.return_value = [
            RegistrarCertification('HOLLY', 1, None), RegistrarCertification('QUEEG', 2, None),
            RegistrarCertification('GORDON', 5, None)]

        response = self.client.get(reverse('webwhois:registrars'))

        self.assertContains(response, "List of registrars")
        self.assertEqual([r['registrar'] for r in response.context['registrars']], [gordon, queeg, holly])
        self.assertEqual(WHOIS.mock_calls,
                         [call.get_registrars(), call.get_registrar_certification_list(), call.get_registrar_groups()])


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(__file__), 'templates')],
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
            size=5
        )
        content = "<html><body>The content.</body></html>"
        FILE_MANAGER.load.return_value.download.return_value = content
        response = self.client.get(reverse("webwhois:download_evaluation_file", kwargs={"handle": "REG-MOJEID"}))
        self.assertEqual(response.content, content.encode())
        self.assertEqual(response['Content-Type'], 'text/html')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="test.html"')
        self.assertEqual(WHOIS.mock_calls, [call.get_registrar_certification_list()])
        self.assertEqual(FILE_MANAGER.mock_calls, [
            call.info(2),
            call.load(2),
            call.load().download(5),
            call.load().finalize_download()
        ])
