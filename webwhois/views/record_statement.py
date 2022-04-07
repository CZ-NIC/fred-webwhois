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
from django.http import Http404, HttpResponse
from django.views.generic import View
from fred_idl.Registry.RecordStatement import OBJECT_DELETE_CANDIDATE, OBJECT_NOT_FOUND

from webwhois.utils.corba_wrapper import LOGGER, RECORD_STATEMENT

from ..constants import LogEntryType, LogResult


class ServeRecordStatementView(View):
    """Serve record statement PDF."""

    log_entry_type = LogEntryType.RECORD_STATEMENT

    def get(self, request, object_type, handle):
        properties = {'handle': handle, 'objectType': object_type, 'documentType': 'public'}
        with LOGGER.create(self.log_entry_type, source_ip=self.request.META.get('REMOTE_ADDR', ''),
                           properties=properties) as log_entry:
            try:
                if object_type == "domain":
                    pdf_content = RECORD_STATEMENT.domain_printout(handle, False)
                elif object_type == "contact":
                    pdf_content = RECORD_STATEMENT.contact_printout(handle, False)
                elif object_type == "nsset":
                    pdf_content = RECORD_STATEMENT.nsset_printout(handle)
                elif object_type == "keyset":
                    pdf_content = RECORD_STATEMENT.keyset_printout(handle)
                else:
                    raise ValueError("Unknown object_type.")
                log_entry.result = LogResult.SUCCESS
            except (OBJECT_NOT_FOUND, OBJECT_DELETE_CANDIDATE) as error:
                log_entry.properties['reason'] = type(error).__name__
                log_entry.result = LogResult.NOT_FOUND
                raise Http404
            except BaseException as error:
                log_entry.properties['exception'] = type(error).__name__
                raise

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="record-statement-{0}-{1}.pdf"'.format(object_type,
                                                                                                       handle)
        return response
