from __future__ import unicode_literals

from django.http import Http404, HttpResponse
from django.views.generic import View
from fred_idl.Registry.RecordStatement import OBJECT_DELETE_CANDIDATE, OBJECT_NOT_FOUND

from webwhois.utils.corba_wrapper import LOGGER, RECORD_STATEMENT
from webwhois.views.public_request_mixin import LoggerMixin


class ServeRecordStatementView(LoggerMixin, View):
    """Serve record statement PDF."""

    service_name = "Web whois"

    def _get_logging_request_name_and_properties(self, data):
        properties = [
            ("handle", data['handle']),
            ("objectType", data['object_type']),
            ("documentType", 'public'),
        ]
        return 'RecordStatement', properties

    def finish_logging_request(self, log_request, error_object):
        """
        Finish logging request.

        @param log_request: Logger instace.
        @param error_object: Error object of python exception or corba exception.
        """
        if log_request is None:
            return
        properties_out, references = [], []
        if error_object:
            if isinstance(error_object, (OBJECT_NOT_FOUND, OBJECT_DELETE_CANDIDATE)):
                properties_out.append(("reason", type(error_object).__name__))
                log_request.result = "NotFound"
            else:
                # Default result is "Error"
                properties_out.append(("exception", error_object.__class__.__name__))
        else:
            log_request.result = "Ok"
        log_request.close(properties=properties_out, references=references)

    def get(self, request, object_type, handle):
        data = {
            'object_type': object_type,
            'handle': handle,
        }
        log_request = self.prepare_logging_request(data) if LOGGER else None
        error_object = None
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
        except (OBJECT_NOT_FOUND, OBJECT_DELETE_CANDIDATE) as err:
            error_object = err
            raise Http404
        except BaseException as err:
            error_object = err
            raise
        finally:
            self.finish_logging_request(log_request, error_object)

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="record-statement-{0}-{1}.pdf"'.format(object_type,
                                                                                                       handle)
        return response
