#
# Copyright (C) 2021-2022  CZ.NIC, z. s. p. o.
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
from datetime import datetime
from unittest import skipIf
from unittest.mock import call, patch, sentinel

from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from fred_idl.Registry.Whois import INTERNAL_SERVER_ERROR, OBJECT_NOT_FOUND, Domain
from grill.utils import TestLogEntry, TestLoggerClient
from grpc import StatusCode
from grpc._channel import _RPCState, _SingleThreadedRendezvous as _Rendezvous
from omniORB import CORBA

try:
    from cdnskey_processor_api.service_report_grpc_pb2 import RawScanResult, RawScanResultsReply
except ImportError:
    RawScanResult = None

from webwhois.constants import LOGGER_SERVICE, CdnskeyStatus, DnskeyAlgorithm, DnskeyFlag, LogEntryType, LogResult
from webwhois.utils import WHOIS

from .test_utils_cdnskey_client import TestCdnskeyClient
from .utils import TEMPLATES


@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
class ScanResultsViewNoBackendTest(SimpleTestCase):
    """Test scan results view without a backend."""
    domain = 'example.org'

    def test_no_backend(self):
        with override_settings(WEBWHOIS_CDNSKEY_NETLOC=None):
            response = self.client.get(reverse('webwhois:scan_results', kwargs={'handle': self.domain}))

        self.assertContains(response, 'not found', status_code=404)


@override_settings(ROOT_URLCONF='webwhois.tests.urls', TEMPLATES=TEMPLATES)
@skipIf(RawScanResult is None, "Only available with cdnskey_processor_api installed.")
class ScanResultsViewTest(SimpleTestCase):
    domain = 'example.org'
    worker = 'kryten'
    scan_at = datetime(2020, 3, 2, 13, tzinfo=timezone.utc)
    nameserver = 'example.net'
    ip_address = '256.0.0.1'
    public_key = 'Quagaars!'
    flags = DnskeyFlag.ZONE
    alg = DnskeyAlgorithm.RSAMD5

    def setUp(self):
        patcher = patch('webwhois.views.scan_results.get_cdnskey_client',
                        return_value=TestCdnskeyClient(sentinel.netloc), autospec=True)
        self.addCleanup(patcher.stop)
        self.get_cdnskey_client_mock = patcher.start()
        self.cdnskey_client = self.get_cdnskey_client_mock.return_value

        whois_patcher = patch.object(WHOIS, 'client', spec=('get_domain_by_handle', ))
        self.addCleanup(whois_patcher.stop)
        whois_patcher.start()
        WHOIS.get_domain_by_handle.return_value = Domain(
            self.domain, None, [], None, None, None, [], datetime(2019, 12, 9, 16, tzinfo=timezone.utc), None, None,
            None, None, None, None, None, None)

        self.test_logger = TestLoggerClient()
        log_patcher = patch('webwhois.utils.corba_wrapper.LOGGER.client', new=self.test_logger)
        self.addCleanup(log_patcher.stop)
        log_patcher.start()

    def _get_scan_result(self, scan_at: datetime = scan_at) -> RawScanResult:
        scan_result = RawScanResult()
        scan_result.worker_name.value = self.worker
        scan_result.scan_at.FromDatetime(scan_at)
        scan_result.nameserver.value = self.nameserver
        scan_result.nameserver_ip.value = self.ip_address
        scan_result.cdnskey.flags.value = self.flags
        scan_result.cdnskey.alg.value = self.alg
        scan_result.cdnskey.public_key.value = self.public_key
        return scan_result

    def test_results(self):
        reply = RawScanResultsReply()
        reply.data.items.append(self._get_scan_result())
        self.cdnskey_client.mock.return_value = [reply]

        response = self.client.get(reverse('webwhois:scan_results', kwargs={'handle': self.domain}))

        self.assertContains(response, 'Scan results')
        cdnskey = {'flags': self.flags, 'alg': self.alg, 'proto': 0, 'public_key': self.public_key,
                   'status': CdnskeyStatus.INSECURE_KEY}
        result = {'worker_name': self.worker, 'scan_at': self.scan_at, 'nameserver_ip': self.ip_address,
                  'nameserver': self.nameserver, 'cdnskey': cdnskey}
        self.assertEqual(response.context['scan_results'], [result])
        self.assertEqual(self.get_cdnskey_client_mock.mock_calls, [call()])

        # Check logger
        log_entry = TestLogEntry(LOGGER_SERVICE, LogEntryType.SCAN_RESULTS, LogResult.SUCCESS, source_ip='127.0.0.1',
                                 input_properties={'domain': self.domain})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())

    def test_results_ordered(self):
        scan_at_after = datetime(2020, 3, 3, 13, tzinfo=timezone.utc)
        scan_at_before = datetime(2020, 3, 1, 13, tzinfo=timezone.utc)
        reply = RawScanResultsReply()
        reply.data.items.append(self._get_scan_result(scan_at=scan_at_after))
        reply.data.items.append(self._get_scan_result())
        reply.data.items.append(self._get_scan_result(scan_at=scan_at_before))
        self.cdnskey_client.mock.return_value = [reply]

        response = self.client.get(reverse('webwhois:scan_results', kwargs={'handle': self.domain}))

        self.assertContains(response, 'Scan results')
        self.assertEqual(response.context['scan_results'][0]['scan_at'], scan_at_before)
        self.assertEqual(response.context['scan_results'][1]['scan_at'], self.scan_at)
        self.assertEqual(response.context['scan_results'][2]['scan_at'], scan_at_after)

    def test_results_truncated(self):
        # Test results are truncated to a time of the domain registration.
        old_scan_at = datetime(2019, 3, 1, 13, tzinfo=timezone.utc)
        reply = RawScanResultsReply()
        reply.data.items.append(self._get_scan_result(scan_at=old_scan_at))
        reply.data.items.append(self._get_scan_result())
        self.cdnskey_client.mock.return_value = [reply]

        response = self.client.get(reverse('webwhois:scan_results', kwargs={'handle': self.domain}))

        self.assertContains(response, 'Scan results')
        self.assertEqual(len(response.context['scan_results']), 1)
        self.assertEqual(response.context['scan_results'][0]['scan_at'], self.scan_at)

    def _test_ignore_whois_error(self, error: CORBA.Exception) -> None:
        WHOIS.get_domain_by_handle.side_effect = error
        reply = RawScanResultsReply()
        reply.data.items.append(self._get_scan_result())
        self.cdnskey_client.mock.return_value = [reply]

        response = self.client.get(reverse('webwhois:scan_results', kwargs={'handle': self.domain}))

        self.assertContains(response, 'Scan results')
        self.assertTrue(response.context['scan_results'])

    def test_ignore_whois_not_found(self):
        # Ignore if domain isn't found in whois backend.
        self._test_ignore_whois_error(OBJECT_NOT_FOUND)

    def test_ignore_whois_server_error(self):
        # Ignore if domain isn't found in whois backend.
        self._test_ignore_whois_error(INTERNAL_SERVER_ERROR)

    def test_ignore_idna_error(self):
        # Ignore errors in IDNA.
        reply = RawScanResultsReply()
        reply.data.items.append(self._get_scan_result())
        self.cdnskey_client.mock.return_value = [reply]

        response = self.client.get(reverse('webwhois:scan_results', kwargs={'handle': '...example.org'}))

        self.assertContains(response, 'Scan results')
        self.assertTrue(response.context['scan_results'])

    def test_no_results(self):
        reply = RawScanResultsReply()
        reply.data.items.extend([])
        self.cdnskey_client.mock.return_value = [reply]

        response = self.client.get(reverse('webwhois:scan_results', kwargs={'handle': self.domain}))

        self.assertContains(response, 'Scan results')
        self.assertEqual(response.context['scan_results'], [])

    def test_not_found(self):
        error = _Rendezvous(_RPCState((), '', '', StatusCode.NOT_FOUND, ""), None, None, None)
        self.cdnskey_client.mock.side_effect = error

        response = self.client.get(reverse('webwhois:scan_results', kwargs={'handle': self.domain}))

        self.assertContains(response, 'not found', status_code=404)

        # Check logger
        log_entry = TestLogEntry(LOGGER_SERVICE, LogEntryType.SCAN_RESULTS, LogResult.NOT_FOUND, source_ip='127.0.0.1',
                                 input_properties={'domain': self.domain})
        self.assertEqual(self.test_logger.mock.mock_calls, log_entry.get_calls())
