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
from unittest.mock import call, patch

from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from fred_idl.Registry.RecordStatement import INTERNAL_SERVER_ERROR, OBJECT_DELETE_CANDIDATE, OBJECT_NOT_FOUND
from grill.utils import TestLogEntry, TestLoggerClient

from webwhois.constants import LOGGER_SERVICE, LogEntryType, LogResult
from webwhois.utils import RECORD_STATEMENT

from .utils import TEMPLATES, apply_patch


@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestRecordStatementPdf(SimpleTestCase):

    def setUp(self):
        spec = ('contact_printout', 'domain_printout', 'keyset_printout', 'nsset_printout')
        apply_patch(self, patch.object(RECORD_STATEMENT, 'client', spec=spec))

        self.test_logger = TestLoggerClient()
        log_patcher = patch('webwhois.utils.corba_wrapper.LOGGER.client', new=self.test_logger)
        self.addCleanup(log_patcher.stop)
        log_patcher.start()

    def test_download_domain(self):
        RECORD_STATEMENT.domain_printout.return_value = "PDF content..."
        response = self.client.get(reverse("webwhois:record_statement_pdf", kwargs={
            "object_type": "domain", "handle": "foo.cz"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'], 'attachment; filename="record-statement-domain-foo.cz.pdf"')
        self.assertEqual(response.content, "PDF content...".encode())
        self.assertEqual(RECORD_STATEMENT.mock_calls, [call.domain_printout('foo.cz', False)])

        # Check logger
        properties = {'handle': 'foo.cz', 'objectType': 'domain', 'documentType': 'public'}
        log_entry = TestLogEntry(LOGGER_SERVICE, LogEntryType.RECORD_STATEMENT, LogResult.SUCCESS,
                                 source_ip='127.0.0.1', input_properties=properties)
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def _assert_download(self, object_name, call_record_statement):
        response = self.client.get(reverse("webwhois:record_statement_pdf", kwargs={
            "object_type": object_name, "handle": "FOO"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'],
                         'attachment; filename="record-statement-%s-FOO.pdf"' % object_name)
        self.assertEqual(response.content, "PDF content...".encode())
        self.assertEqual(RECORD_STATEMENT.mock_calls, [call_record_statement])

        # Check logger
        properties = {'handle': 'FOO', 'objectType': object_name, 'documentType': 'public'}
        log_entry = TestLogEntry(LOGGER_SERVICE, LogEntryType.RECORD_STATEMENT, LogResult.SUCCESS,
                                 source_ip='127.0.0.1', input_properties=properties)
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_download_contact(self):
        RECORD_STATEMENT.contact_printout.return_value = "PDF content..."
        self._assert_download("contact", call.contact_printout('FOO', False))

    def test_download_nsset(self):
        RECORD_STATEMENT.nsset_printout.return_value = "PDF content..."
        self._assert_download("nsset", call.nsset_printout('FOO'))

    def test_download_keyset(self):
        RECORD_STATEMENT.keyset_printout.return_value = "PDF content..."
        self._assert_download("keyset", call.keyset_printout('FOO'))

    def _test_no_record_found(self, exception, exception_name):
        # Test for cases which result in page not found.
        RECORD_STATEMENT.domain_printout.side_effect = exception

        response = self.client.get(
            reverse("webwhois:record_statement_pdf", kwargs={"object_type": "domain", "handle": "foo.cz"}))

        self.assertContains(response, 'Not Found', status_code=404)
        self.assertEqual(RECORD_STATEMENT.mock_calls, [call.domain_printout('foo.cz', False)])

        # Check logger
        properties = {'handle': 'foo.cz', 'objectType': 'domain', 'documentType': 'public'}
        log_entry = TestLogEntry(LOGGER_SERVICE, LogEntryType.RECORD_STATEMENT, LogResult.NOT_FOUND,
                                 source_ip='127.0.0.1', input_properties=properties,
                                 properties={'reason': exception_name})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_object_not_found(self):
        self._test_no_record_found(OBJECT_NOT_FOUND, 'OBJECT_NOT_FOUND')

    def test_object_delete_candidate(self):
        self._test_no_record_found(OBJECT_DELETE_CANDIDATE, 'OBJECT_DELETE_CANDIDATE')

    def test_download_domain_internal_server_error(self):
        RECORD_STATEMENT.domain_printout.side_effect = INTERNAL_SERVER_ERROR
        with self.assertRaises(INTERNAL_SERVER_ERROR):
            self.client.get(reverse("webwhois:record_statement_pdf", kwargs={
                "object_type": "domain", "handle": "foo.cz"}))
        self.assertEqual(RECORD_STATEMENT.mock_calls, [call.domain_printout('foo.cz', False)])

        # Check logger
        properties = {'handle': 'foo.cz', 'objectType': 'domain', 'documentType': 'public'}
        log_entry = TestLogEntry(LOGGER_SERVICE, LogEntryType.RECORD_STATEMENT, LogResult.ERROR,
                                 source_ip='127.0.0.1', input_properties=properties,
                                 properties={'exception': 'INTERNAL_SERVER_ERROR'})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_unknown_object_type(self):
        with self.assertRaises(ValueError):
            self.client.get(reverse("test_record_statement_pdf", kwargs={
                "object_type": "foo", "handle": "foo.cz"}))
