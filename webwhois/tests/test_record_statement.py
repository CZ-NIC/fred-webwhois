#
# Copyright (C) 2017-2022  CZ.NIC, z. s. p. o.
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
#
from io import BytesIO
from unittest.mock import _Call, call, patch

from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from grill.utils import TestLogEntry, TestLoggerClient
from regal.exceptions import DomainDoesNotExist

from webwhois.constants import LOGGER_SERVICE, LogEntryType, LogResult

from .utils import TEMPLATES


@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestRecordStatementPdf(SimpleTestCase):

    def setUp(self):
        patcher = patch('webwhois.views.record_statement.STATEMENTOR', autospec=True)
        self.addCleanup(patcher.stop)
        self.statementor_mock = patcher.start()

        self.test_logger = TestLoggerClient()
        log_patcher = patch('webwhois.utils.corba_wrapper.LOGGER.client', new=self.test_logger)
        self.addCleanup(log_patcher.stop)
        log_patcher.start()

    def _test_download(self, object_name: str, statement_call: _Call) -> None:
        response = self.client.get(
            reverse("webwhois:record_statement_pdf", kwargs={"object_type": object_name, "handle": "FOO"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'],
                         'attachment; filename="record-statement-%s-FOO.pdf"' % object_name)
        self.assertEqual(response.content, b"PDF content...")
        self.assertEqual(self.statementor_mock.mock_calls, [statement_call])

        # Check logger
        properties = {'handle': 'FOO', 'objectType': object_name, 'documentType': 'public'}
        log_entry = TestLogEntry(LOGGER_SERVICE, LogEntryType.RECORD_STATEMENT, LogResult.SUCCESS,
                                 source_ip='127.0.0.1', input_properties=properties)
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_download_contact(self):
        self.statementor_mock.get_contact_statement.return_value = BytesIO(b"PDF content...")
        self._test_download("contact", call.get_contact_statement('FOO'))

    def test_download_domain(self):
        self.statementor_mock.get_domain_statement.return_value = BytesIO(b"PDF content...")
        self._test_download("domain", call.get_domain_statement('FOO'))

    def test_download_keyset(self):
        self.statementor_mock.get_keyset_statement.return_value = BytesIO(b"PDF content...")
        self._test_download("keyset", call.get_keyset_statement('FOO'))

    def test_download_nsset(self):
        self.statementor_mock.get_nsset_statement.return_value = BytesIO(b"PDF content...")
        self._test_download("nsset", call.get_nsset_statement('FOO'))

    def test_object_does_not_exist(self):
        # Test for cases which result in page not found.
        self.statementor_mock.get_domain_statement.side_effect = DomainDoesNotExist

        response = self.client.get(
            reverse("webwhois:record_statement_pdf", kwargs={"object_type": "domain", "handle": "foo.cz"}))

        self.assertContains(response, 'Not Found', status_code=404)
        self.assertEqual(self.statementor_mock.mock_calls, [call.get_domain_statement('foo.cz')])

        # Check logger
        properties = {'handle': 'foo.cz', 'objectType': 'domain', 'documentType': 'public'}
        log_entry = TestLogEntry(LOGGER_SERVICE, LogEntryType.RECORD_STATEMENT, LogResult.NOT_FOUND,
                                 source_ip='127.0.0.1', input_properties=properties,
                                 properties={'reason': 'DomainDoesNotExist'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_download_domain_internal_server_error(self):
        self.statementor_mock.get_domain_statement.side_effect = ValueError("Gazpacho!")
        with self.assertRaisesRegexp(ValueError, 'Gazpacho!'):
            self.client.get(
                reverse("webwhois:record_statement_pdf", kwargs={"object_type": "domain", "handle": "foo.cz"}))
        self.assertEqual(self.statementor_mock.mock_calls, [call.get_domain_statement('foo.cz')])

        # Check logger
        properties = {'handle': 'foo.cz', 'objectType': 'domain', 'documentType': 'public'}
        log_entry = TestLogEntry(LOGGER_SERVICE, LogEntryType.RECORD_STATEMENT, LogResult.ERROR,
                                 source_ip='127.0.0.1', input_properties=properties,
                                 properties={'exception': 'ValueError'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_unknown_object_type(self):
        with self.assertRaises(ValueError):
            self.client.get(reverse("test_record_statement_pdf", kwargs={
                "object_type": "foo", "handle": "foo.cz"}))
