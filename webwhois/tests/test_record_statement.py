from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.test import SimpleTestCase, override_settings
from fred_idl.Registry.RecordStatement import INTERNAL_SERVER_ERROR, OBJECT_DELETE_CANDIDATE, OBJECT_NOT_FOUND
from mock import call, patch

from webwhois.utils import RECORD_STATEMENT

from .utils import CALL_BOOL, TEMPLATES, apply_patch


@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class TestRecordStatementPdf(SimpleTestCase):

    def setUp(self):
        spec = ('contact_printout', 'domain_printout', 'keyset_printout', 'nsset_printout')
        apply_patch(self, patch.object(RECORD_STATEMENT, 'client', spec=spec))
        self.LOGGER = apply_patch(self, patch("webwhois.views.record_statement.LOGGER"))
        apply_patch(self, patch("webwhois.views.logger_mixin.LOGGER", self.LOGGER))
        self.LOGGER.create_request.return_value.result = 'Error'

    def test_download_domain(self):
        RECORD_STATEMENT.domain_printout.return_value = "PDF content..."
        response = self.client.get(reverse("webwhois:record_statement_pdf", kwargs={
            "object_type": "domain", "handle": "foo.cz"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'], 'attachment; filename="record-statement-domain-foo.cz.pdf"')
        self.assertEqual(response.content, "PDF content...".encode())
        self.assertEqual(RECORD_STATEMENT.mock_calls, [call.domain_printout('foo.cz', False)])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Web whois', 'RecordStatement', properties=[
                ('handle', 'foo.cz'),
                ('objectType', 'domain'),
                ('documentType', 'public')
            ]),
            call().close(properties=[], references=[])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')

    def _assert_download(self, object_name, call_record_statement):
        response = self.client.get(reverse("webwhois:record_statement_pdf", kwargs={
            "object_type": object_name, "handle": "FOO"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'],
                         'attachment; filename="record-statement-%s-FOO.pdf"' % object_name)
        self.assertEqual(response.content, "PDF content...".encode())
        self.assertEqual(RECORD_STATEMENT.mock_calls, [call_record_statement])
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Web whois', 'RecordStatement', properties=[
                ('handle', 'FOO'),
                ('objectType', object_name),
                ('documentType', 'public')
            ]),
            call().close(properties=[], references=[]),
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')

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
        self.LOGGER.create_request.return_value.request_id = 42
        RECORD_STATEMENT.domain_printout.side_effect = exception

        response = self.client.get(
            reverse("webwhois:record_statement_pdf", kwargs={"object_type": "domain", "handle": "foo.cz"}))

        self.assertContains(response, 'Not Found', status_code=404)
        self.assertEqual(RECORD_STATEMENT.mock_calls, [call.domain_printout('foo.cz', False)])
        calls = [call('127.0.0.1', 'Web whois', 'RecordStatement',
                      properties=[('handle', 'foo.cz'), ('objectType', 'domain'), ('documentType', 'public')]),
                 call().close(properties=[('reason', exception_name)], references=[])]
        self.assertEqual(self.LOGGER.create_request.mock_calls, calls)
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'NotFound')

    def test_object_not_found(self):
        self._test_no_record_found(OBJECT_NOT_FOUND, 'OBJECT_NOT_FOUND')

    def test_object_delete_candidate(self):
        self._test_no_record_found(OBJECT_DELETE_CANDIDATE, 'OBJECT_DELETE_CANDIDATE')

    def test_download_domain_internal_server_error(self):
        self.LOGGER.create_request.return_value.request_id = 42
        RECORD_STATEMENT.domain_printout.side_effect = INTERNAL_SERVER_ERROR
        with self.assertRaises(INTERNAL_SERVER_ERROR):
            self.client.get(reverse("webwhois:record_statement_pdf", kwargs={
                "object_type": "domain", "handle": "foo.cz"}))
        self.assertEqual(RECORD_STATEMENT.mock_calls, [call.domain_printout('foo.cz', False)])
        self.assertEqual(self.LOGGER.mock_calls, [
            CALL_BOOL,
            call.create_request('127.0.0.1', 'Web whois', 'RecordStatement', properties=[
                ('handle', 'foo.cz'),
                ('objectType', 'domain'),
                ('documentType', 'public')
            ]),
            call.create_request().close(properties=[('exception', 'INTERNAL_SERVER_ERROR')], references=[])
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Error')

    def test_unknown_object_type(self):
        with self.assertRaises(ValueError):
            self.client.get(reverse("test_record_statement_pdf", kwargs={
                "object_type": "foo", "handle": "foo.cz"}))


@override_settings(ROOT_URLCONF='webwhois.tests.urls')
class TestRecordStatementNoLogger(SimpleTestCase):

    def setUp(self):
        spec = ('contact_printout', 'domain_printout', 'keyset_printout', 'nsset_printout')
        apply_patch(self, patch.object(RECORD_STATEMENT, 'client', spec=spec))
        self.LOGGER = apply_patch(self, patch("webwhois.views.record_statement.LOGGER", None))
        apply_patch(self, patch("webwhois.views.logger_mixin.LOGGER", self.LOGGER))

    def test_download_domain(self):
        RECORD_STATEMENT.domain_printout.return_value = "PDF content..."
        response = self.client.get(reverse("webwhois:record_statement_pdf", kwargs={
            "object_type": "domain", "handle": "foo.cz"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertEqual(response['content-disposition'], 'attachment; filename="record-statement-domain-foo.cz.pdf"')
        self.assertEqual(response.content, "PDF content...".encode())
        self.assertEqual(RECORD_STATEMENT.mock_calls, [call.domain_printout('foo.cz', False)])
