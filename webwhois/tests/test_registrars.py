#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2018  CZ.NIC, z. s. p. o.
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

from __future__ import unicode_literals

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
from webwhois.tests.utils import CALL_BOOL, TEMPLATES, apply_patch
from webwhois.utils import FILE_MANAGER, WHOIS


@patch('webwhois.views.registrar.WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED', ['certified'])
@patch('webwhois.views.registrar.WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED', ['uncertified'])
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

    def test_registrars_retail(self):
        WHOIS.get_registrar_groups.return_value = self._get_registrar_groups()
        WHOIS.get_registrar_certification_list.return_value = self._get_registrar_certs()
        WHOIS.get_registrars.return_value = self._get_registrars()
        response = self.client.get(reverse("webwhois:registrar_list_retail"))
        self.assertContains(response, "Registrars offering also retail services")
        self.assertTrue(response.context['is_retail'])
        self.assertEqual(response.context['registrars'][0]['score'], 8)
        self.assertEqual(response.context['registrars'][1]['score'], 2)
        self.assertEqual(response.context['registrars'][2]['score'], 0)
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
        self.assertFalse(response.context['is_retail'])
        self.assertEqual(self.LOGGER.mock_calls, [])
        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars()
        ])

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

        self.assertContains(response, "Registrars offering also retail services")
        self.assertEqual(response.context['registrars'][0]['registrar'].handle, 'REG-ACTIVE')
        self.assertEqual(response.context['registrars'][1]['registrar'].handle, 'REG-DEACTIVE')
        self.assertEqual(response.context['registrars'][2]['registrar'].handle, 'REG-MOJEID')

        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars(),
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
class TestRegistrarsUnknownGroupNames(SetMocksMixin, GetRegistryObjectMixin, SimpleTestCase):

    def test_registrars_retail(self):
        response = self.client.get(reverse("webwhois:registrar_list_retail"))
        self.assertContains(response, "Registrars offering also retail services")
        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars()
        ])

    def test_registrars_wholesale(self):
        response = self.client.get(reverse("webwhois:registrar_list_wholesale"))
        self.assertContains(response, "Registrars offering only wholesale services")
        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars()
        ])


@patch('webwhois.views.registrar.WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED', [])
@patch('webwhois.views.registrar.WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED', [])
@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestRegistrarsEmptyGroupNames(SetMocksMixin, GetRegistryObjectMixin, SimpleTestCase):

    def test_registrars_retail(self):
        response = self.client.get(reverse("webwhois:registrar_list_retail"))
        self.assertContains(response, "Registrars offering also retail services")
        self.assertEqual(WHOIS.mock_calls, [
            call.get_registrar_groups(),
            call.get_registrar_certification_list(),
            call.get_registrars()
        ])

    def test_registrars_wholesale(self):
        response = self.client.get(reverse("webwhois:registrar_list_wholesale"))
        self.assertContains(response, "Registrars offering only wholesale services")
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
