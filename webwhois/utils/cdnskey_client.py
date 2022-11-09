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
"""Utilities for cdnskey processor client."""
import itertools
from functools import lru_cache
from typing import Any, Dict, Iterable, Optional

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from grpc import ChannelCredentials, RpcError, StatusCode, ssl_channel_credentials

try:
    from cdnskey_processor_api import service_report_grpc_pb2_grpc
    from cdnskey_processor_api.common_types_pb2 import (Cdnskey, CdnskeyStatus as CdnskeyStatusProto, DnskeyAlg,
                                                        DnskeyFlags)
    from cdnskey_processor_api.service_report_grpc_pb2 import RawScanResultsRequest
    from frgal import GrpcClient, GrpcDecoder
except ImportError:
    Cdnskey, DnskeyAlg, DnskeyFlags = None, None, None

    class GrpcDecoder:  # type: ignore[no-redef]
        pass

    class GrpcClient:  # type: ignore[no-redef]
        pass

from webwhois.settings import WEBWHOIS_SETTINGS

from ..constants import CdnskeyStatus, DnskeyAlgorithm, DnskeyFlag


class CdnskeyDecoder(GrpcDecoder):
    """Decoder for cdnskey client."""

    def __init__(self) -> None:
        super().__init__()
        self.set_decoder(DnskeyFlags, self._decode_dnskey_flag)
        self.set_decoder(DnskeyAlg, self._decode_dnskey_algorithm)
        self.set_decoder(Cdnskey, self._decode_cdnskey)

    def _decode_dnskey_flag(self, value: DnskeyFlags) -> DnskeyFlag:  # type: ignore[valid-type]
        return DnskeyFlag(value.value)  # type: ignore[operator, no-any-return]

    def _decode_dnskey_algorithm(self, value: DnskeyAlg) -> DnskeyAlgorithm:  # type: ignore[valid-type]
        return DnskeyAlgorithm(value.value)  # type: ignore[operator, no-any-return]

    def _decode_cdnskey(self, value: Cdnskey):
        decoded = self._decode_message(value)
        # Decode status to enum.
        decoded['status'] = CdnskeyStatus(CdnskeyStatusProto.Name(decoded['status']))  # type: ignore[call-arg]
        return decoded


class CdnskeyClient(GrpcClient):
    """gRPC client for cdnskey processor."""

    grpc_service = 'Report'

    def __init__(self, netloc: str, credentials: Optional[ChannelCredentials] = None):
        """Initialize identity client.

        Arguments:
            netloc: Network location of a gRPC server.
            credentials: Credentials for a secure channel connection. If None, insecure channel is used.
        """
        decoder = CdnskeyDecoder()
        super().__init__(netloc, decoder=decoder, grpc_modules=[service_report_grpc_pb2_grpc],
                         credentials=credentials)

    def raw_scan_results(self, domain: str) -> Iterable[Dict[str, Any]]:
        """Return scan results for a domain."""
        request = RawScanResultsRequest()
        request.domain_fqdn.value = domain
        try:
            response_data = self.call_stream(self.grpc_service, 'raw_scan_results', request)
            return itertools.chain.from_iterable(response_data)
        except RpcError as error:
            if error.code() == StatusCode.NOT_FOUND:
                raise Http404("Domain '{}' not found.".format(domain)) from error
            raise error


@lru_cache()
def get_cdnskey_client() -> Optional[CdnskeyClient]:
    """Return the client instance.

    Utility function to cache the client instance.
    """
    if not WEBWHOIS_SETTINGS.CDNSKEY_NETLOC:
        return None
    if Cdnskey is None:
        raise ImproperlyConfigured("WEBWHOIS_CDNSKEY_NETLOC is installed, but cdnskey_processor_api is not available.")
    credentials = None
    if WEBWHOIS_SETTINGS.CDNSKEY_SSL_CERT:
        with open(WEBWHOIS_SETTINGS.CDNSKEY_SSL_CERT) as file:
            credentials = ssl_channel_credentials(file.read())
    return CdnskeyClient(WEBWHOIS_SETTINGS.CDNSKEY_NETLOC, credentials=credentials)
