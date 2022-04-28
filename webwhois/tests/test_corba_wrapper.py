#!/usr/bin/python
#
# Copyright (C) 2016-2022  CZ.NIC, z. s. p. o.
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
from datetime import datetime
from unittest.mock import call, patch, sentinel

import omniORB
from django.test import SimpleTestCase
from django.utils import timezone
from fred_idl.ccReg import FileManager, _objref_FileDownload
from fred_idl.Registry import Buffer, IsoDateTime
from fred_idl.Registry.Whois import WhoisIntf

from webwhois.utils.corba_wrapper import WebwhoisCorbaRecoder, load_filemanager_from_idl, load_whois_from_idl

from .utils import apply_patch


class TestWebwhoisCorbaRecoder(SimpleTestCase):
    """
    Tests for `WebwhoisCorbaRecoder`.
    """

    def test_decode_buffer(self):
        buffer_obj = Buffer('foo')
        self.assertEqual(WebwhoisCorbaRecoder().decode(buffer_obj), 'foo')

    def test_decode_file_download(self):
        if omniORB.__version__ < '4':  # pragma: no cover
            file_download = _objref_FileDownload()
        else:  # pragma: no cover
            file_download = _objref_FileDownload(sentinel.object)
        self.assertEqual(WebwhoisCorbaRecoder().decode(file_download), file_download)

    def test_encode_file_download(self):
        if omniORB.__version__ < '4':  # pragma: no cover
            file_download = _objref_FileDownload()
        else:  # pragma: no cover
            file_download = _objref_FileDownload(sentinel.object)
        self.assertEqual(WebwhoisCorbaRecoder().encode(file_download), file_download)

    def test_decode_isodatetime_aware(self):
        recoder = WebwhoisCorbaRecoder()
        with self.settings(USE_TZ=True):
            self.assertEqual(recoder.decode(IsoDateTime('2001-02-03T12:13:14Z')),
                             datetime(2001, 2, 3, 12, 13, 14, tzinfo=timezone.utc))

    def test_decode_isodatetime_naive(self):
        recoder = WebwhoisCorbaRecoder()
        with self.settings(USE_TZ=False, TIME_ZONE='Europe/Prague'):
            self.assertEqual(recoder.decode(IsoDateTime('2001-02-03T12:13:14Z')),
                             datetime(2001, 2, 3, 13, 13, 14))


class TestLoadIdl(SimpleTestCase):

    def setUp(self):
        patcher = patch('webwhois.utils.corba_wrapper._CLIENT')
        self.corba_mock = apply_patch(self, patcher)
        self.corba_mock.get_object.return_value = sentinel.corba_object

    def test_load_whois_from_idl(self):
        result = load_whois_from_idl()

        self.assertEqual(result, sentinel.corba_object)
        self.assertEqual(self.corba_mock.mock_calls, [call.get_object('Whois2', WhoisIntf)])

    def test_load_filemanager_from_idl(self):
        result = load_filemanager_from_idl()

        self.assertEqual(result, sentinel.corba_object)
        self.assertEqual(self.corba_mock.mock_calls, [call.get_object('FileManager', FileManager)])
