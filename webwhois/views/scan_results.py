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
"""Views for cdnskey scan results."""
import operator
from datetime import datetime
from typing import Any, Dict, Optional, cast

import idna
from django.http import Http404
from django.views.generic import TemplateView
from omniORB import CORBA

from webwhois.utils import WHOIS
from webwhois.utils.corba_wrapper import LOGGER

from ..constants import LogEntryType, LogResult
from ..utils.cdnskey_client import get_cdnskey_client
from .base import BaseContextMixin


class ScanResultsView(BaseContextMixin, TemplateView):
    """Provides a list of results from cdnskey scan results."""

    template_name = 'webwhois/scan_results.html'
    request_type = LogEntryType.SCAN_RESULTS
    result_success = LogResult.SUCCESS
    result_not_found = LogResult.NOT_FOUND

    def get_domain_registered(self, handle: str) -> Optional[datetime]:
        """Return domain registration datetime."""
        try:
            idna_handle = idna.encode(handle).decode()
        except idna.IDNAError:
            return None

        try:
            domain = WHOIS.get_domain_by_handle(idna_handle)
        except CORBA.Exception:
            return None
        return cast(datetime, domain.registered)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = cast(Dict[str, Any], super().get_context_data(**kwargs))

        client = get_cdnskey_client()
        if client is None:
            raise Http404('Cdnskey processor not defined.')

        with LOGGER.create(self.request_type, source_ip=self.request.META.get('REMOTE_ADDR', ''),
                           properties={'domain': self.kwargs['handle']}) as log_entry:
            try:
                scan_results = client.raw_scan_results(self.kwargs['handle'])
                domain_registered = self.get_domain_registered(self.kwargs['handle'])
                if domain_registered:
                    scan_results = (r for r in scan_results if r['scan_at'] >= domain_registered)
                context['scan_results'] = sorted(scan_results, key=operator.itemgetter('scan_at'))
                log_entry.result = self.result_success
            except Http404:
                log_entry.result = self.result_not_found
                raise
        return context
