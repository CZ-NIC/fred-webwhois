#
# Copyright (C) 2021  CZ.NIC, z. s. p. o.
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
from tempfile import NamedTemporaryFile
from typing import Dict, List, Sequence, Type
from unittest import skipIf
from unittest.mock import call, patch, sentinel

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.utils import timezone
from grpc import RpcError, StatusCode
from grpc._channel import _RPCState, _SingleThreadedRendezvous as _Rendezvous

try:
    from cdnskey_processor_api.common_types_pb2 import (Cdnskey, CdnskeyStatus as CdnskeyStatusProto, DnskeyAlg,
                                                        DnskeyFlags)
    from cdnskey_processor_api.service_report_grpc_pb2 import RawScanResult, RawScanResultsReply, RawScanResultsRequest
    from frgal.utils import TestClientMixin
except ImportError:
    Cdnskey = None
    RawScanResult, RawScanResultsReply = None, None

    class TestClientMixin:  # type: ignore[no-redef]
        pass

from webwhois.constants import CdnskeyStatus, DnskeyAlgorithm, DnskeyFlag
from webwhois.utils.cdnskey_client import CdnskeyClient, CdnskeyDecoder, get_cdnskey_client


@skipIf(Cdnskey is None, "Only available with cdnskey_processor_api installed.")
class CdnskeyDecoderTest(SimpleTestCase):
    def test_decode_flags(self):
        decoder = CdnskeyDecoder()
        data = (
            # message, result
            (DnskeyFlags(value=0), DnskeyFlag(0)),  # type: ignore[operator]
            (DnskeyFlags(value=DnskeyFlag.SECURE_ENTRY_POINT), DnskeyFlag.SECURE_ENTRY_POINT),
            (DnskeyFlags(value=DnskeyFlag.ZONE), DnskeyFlag.ZONE),
            (DnskeyFlags(value=42), DnskeyFlag(42)),  # type: ignore[operator]
        )
        for message, result in data:
            with self.subTest(message=message):
                decoded = decoder.decode(message)
                self.assertEqual(decoded, result)
                self.assertIsInstance(decoded, DnskeyFlag)

    def test_decode_algorithm(self):
        decoder = CdnskeyDecoder()
        data = (
            # message, result
            (DnskeyAlg(value=DnskeyAlgorithm.DELETE_DS), DnskeyAlgorithm.DELETE_DS),
            (DnskeyAlg(value=DnskeyAlgorithm.RSASHA512), DnskeyAlgorithm.RSASHA512),
            (DnskeyAlg(value=DnskeyAlgorithm.INDIRECT), DnskeyAlgorithm.INDIRECT),
            (DnskeyAlg(value=42), DnskeyAlgorithm(42)),  # type: ignore[operator]
        )
        for message, result in data:
            with self.subTest(message=message):
                decoded = decoder.decode(message)
                self.assertEqual(decoded, result)
                self.assertIsInstance(decoded, DnskeyAlgorithm)

    def test_decode_cdnskey(self):
        decoder = CdnskeyDecoder()
        data = (
            # message, result
            (Cdnskey(), {'status': CdnskeyStatus.INSECURE_KEY, 'flags': 0, 'proto': 0, 'alg': 0, 'public_key': None}),
            (Cdnskey(status=CdnskeyStatusProto.UNTRUSTWORTHY),
             {'status': CdnskeyStatus.UNTRUSTWORTHY, 'flags': 0, 'proto': 0, 'alg': 0, 'public_key': None}),
        )
        for message, result in data:
            with self.subTest(message=message):
                decoded = decoder.decode(message)
                self.assertEqual(decoded, result)
                self.assertIsInstance(decoded['status'], CdnskeyStatus)


class TestCdnskeyClient(TestClientMixin, CdnskeyClient):
    """Testing version of an CdnskeyClient."""


@skipIf(Cdnskey is None, "Only available with cdnskey_processor_api installed.")
class CdnskeyClientTest(SimpleTestCase):
    scan_at = datetime(2020, 3, 2, 13, tzinfo=timezone.utc)
    public_key = 'Quagaars!'
    nameserver = 'example.net'

    def setUp(self):
        self.client = TestCdnskeyClient(sentinel.netloc)

    def _get_scan_result(self, worker_name: str, ip_address: str, flags: int, alg: int) -> RawScanResult:
        scan_result = RawScanResult()
        scan_result.worker_name.value = worker_name
        scan_result.scan_at.FromDatetime(self.scan_at)
        scan_result.nameserver.value = self.nameserver
        scan_result.nameserver_ip.value = ip_address
        scan_result.cdnskey.flags.value = flags
        scan_result.cdnskey.alg.value = alg
        scan_result.cdnskey.public_key.value = self.public_key
        return scan_result

    def _test_raw_scan_results(self, replies: List[RawScanResultsReply], results: Sequence[Dict]) -> None:
        self.client.mock.return_value = replies
        domain = 'example.org'

        scan_result = self.client.raw_scan_results(domain)

        self.assertEqual(list(scan_result), results)
        request = RawScanResultsRequest()
        request.domain_fqdn.value = domain
        self.assertEqual(
            self.client.mock.mock_calls,
            [call(request, method='/CdnskeyProcessor.Api.Report.Report/raw_scan_results', timeout=None)])

    def test_raw_scan_results_empty(self):
        self._test_raw_scan_results([], [])

    def test_raw_scan_results(self):
        worker = 'kryten'
        ip_address = '256.0.0.1'
        reply = RawScanResultsReply()
        reply.data.items.append(self._get_scan_result(worker, ip_address, DnskeyFlag.ZONE, DnskeyAlgorithm.RSAMD5))
        replies = [reply]
        cdnskey = {'flags': DnskeyFlag.ZONE, 'alg': DnskeyAlgorithm.RSAMD5, 'proto': 0, 'public_key': self.public_key,
                   'status': CdnskeyStatus.INSECURE_KEY}
        result = {'worker_name': worker, 'scan_at': self.scan_at, 'nameserver_ip': ip_address,
                  'nameserver': self.nameserver, 'cdnskey': cdnskey}
        self._test_raw_scan_results(replies, [result])

    def test_raw_scan_results_multiple(self):
        worker = 'kryten'
        ip_address = '256.0.0.1'
        reply = RawScanResultsReply()
        reply.data.items.append(self._get_scan_result(worker, ip_address, DnskeyFlag.ZONE, DnskeyAlgorithm.RSAMD5))
        reply.data.items.append(self._get_scan_result(worker, ip_address, DnskeyFlag.ZONE, DnskeyAlgorithm.DSA))
        replies = [reply]
        cdnskey_1 = {'flags': DnskeyFlag.ZONE, 'alg': DnskeyAlgorithm.RSAMD5, 'proto': 0, 'public_key': self.public_key,
                     'status': CdnskeyStatus.INSECURE_KEY}
        result_1 = {'worker_name': worker, 'scan_at': self.scan_at, 'nameserver_ip': ip_address,
                    'nameserver': self.nameserver, 'cdnskey': cdnskey_1}
        cdnskey_2 = {'flags': DnskeyFlag.ZONE, 'alg': DnskeyAlgorithm.DSA, 'proto': 0, 'public_key': self.public_key,
                     'status': CdnskeyStatus.INSECURE_KEY}
        result_2 = {'worker_name': worker, 'scan_at': self.scan_at, 'nameserver_ip': ip_address,
                    'nameserver': self.nameserver, 'cdnskey': cdnskey_2}
        self._test_raw_scan_results(replies, [result_1, result_2])

    def test_raw_scan_results_chunked(self):
        worker = 'kryten'
        ip_address = '256.0.0.1'
        reply_1 = RawScanResultsReply()
        reply_1.data.items.append(self._get_scan_result(worker, ip_address, DnskeyFlag.ZONE, DnskeyAlgorithm.RSAMD5))
        reply_2 = RawScanResultsReply()
        reply_2.data.items.append(self._get_scan_result(worker, ip_address, DnskeyFlag.ZONE, DnskeyAlgorithm.DSA))
        replies = [reply_1, reply_2]
        cdnskey_1 = {'flags': DnskeyFlag.ZONE, 'alg': DnskeyAlgorithm.RSAMD5, 'proto': 0, 'public_key': self.public_key,
                     'status': CdnskeyStatus.INSECURE_KEY}
        result_1 = {'worker_name': worker, 'scan_at': self.scan_at, 'nameserver_ip': ip_address,
                    'nameserver': self.nameserver, 'cdnskey': cdnskey_1}
        cdnskey_2 = {'flags': DnskeyFlag.ZONE, 'alg': DnskeyAlgorithm.DSA, 'proto': 0, 'public_key': self.public_key,
                     'status': CdnskeyStatus.INSECURE_KEY}
        result_2 = {'worker_name': worker, 'scan_at': self.scan_at, 'nameserver_ip': ip_address,
                    'nameserver': self.nameserver, 'cdnskey': cdnskey_2}
        self._test_raw_scan_results(replies, [result_1, result_2])

    def _test_raw_scan_results_error(self, status: StatusCode, error_cls: Type[Exception], error_msg: str) -> None:
        domain = 'example.org'
        error = _Rendezvous(_RPCState((), '', '', status, ""), None, None, None)
        self.client.mock.side_effect = error

        with self.assertRaisesRegex(error_cls, error_msg):
            self.client.raw_scan_results(domain)

        request = RawScanResultsRequest()
        request.domain_fqdn.value = domain
        self.assertEqual(
            self.client.mock.mock_calls,
            [call(request, method='/CdnskeyProcessor.Api.Report.Report/raw_scan_results', timeout=None)])

    def test_raw_scan_results_not_found(self):
        self._test_raw_scan_results_error(StatusCode.NOT_FOUND, Http404, "Domain 'example.org' not found.")

    def test_raw_scan_results_error(self):
        self._test_raw_scan_results_error(StatusCode.UNKNOWN, RpcError, 'StatusCode.UNKNOWN')


class GetClientTest(SimpleTestCase):
    def setUp(self):
        get_cdnskey_client.cache_clear()

    def tearDown(self):
        get_cdnskey_client.cache_clear()

    def test_disabled(self):
        with override_settings(WEBWHOIS_CDNSKEY_NETLOC=None):
            self.assertIsNone(get_cdnskey_client())

    @skipIf(Cdnskey, "Only available with cdnskey_processor_api not installed.")
    def test_missing(self):
        # Test cdnskey is set up, but api is missing.
        msg = "WEBWHOIS_CDNSKEY_NETLOC is installed, but cdnskey_processor_api is not available"
        with override_settings(WEBWHOIS_CDNSKEY_NETLOC=sentinel.netloc):
            with self.assertRaisesRegex(ImproperlyConfigured, msg):
                get_cdnskey_client()

    @skipIf(Cdnskey is None, "Only available with cdnskey_processor_api installed.")
    def test_netloc(self):
        with override_settings(WEBWHOIS_CDNSKEY_NETLOC=sentinel.netloc):
            del settings.WEBWHOIS_CDNSKEY_SSL_CERT
            with patch('webwhois.utils.cdnskey_client.CdnskeyClient', return_value=sentinel.client) as client_mock:
                self.assertEqual(get_cdnskey_client(), sentinel.client)

        self.assertEqual(client_mock.mock_calls, [call(sentinel.netloc, credentials=None)])

    @skipIf(Cdnskey is None, "Only available with cdnskey_processor_api installed.")
    def test_ssl_cert(self):
        tmp_file = NamedTemporaryFile()
        tmp_file.write(b'Gazpacho!')
        tmp_file.seek(0)

        with override_settings(WEBWHOIS_CDNSKEY_NETLOC=sentinel.netloc, WEBWHOIS_CDNSKEY_SSL_CERT=tmp_file.name):
            with patch('webwhois.utils.cdnskey_client.CdnskeyClient', return_value=sentinel.client) as client_mock:
                with patch('webwhois.utils.cdnskey_client.ssl_channel_credentials',
                           return_value=sentinel.credentials) as credentials_mock:
                    self.assertEqual(get_cdnskey_client(), sentinel.client)

        self.assertEqual(client_mock.mock_calls, [call(sentinel.netloc, credentials=sentinel.credentials)])
        self.assertEqual(credentials_mock.mock_calls, [call('Gazpacho!')])
