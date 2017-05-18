from django.core.cache import cache
from django.utils.crypto import get_random_string
from django.utils.timezone import now as timezone_now
from django.views.generic import FormView

from webwhois.utils.corba_wrapper import LOGGER, REGISTRY_MODULE
from webwhois.views.logger_mixin import LoggerMixin


class PublicRequestKnownException(Exception):
    """Used for displaying message on the form."""

    def __init__(self, exception_code_name):
        self.exception_code_name = exception_code_name


class PublicRequestLoggerMixin(LoggerMixin):
    """Mixin for logging request if LOGGER is set."""

    service_name = "Public Request"

    def finish_logging_request(self, log_request, response_id, error_object):
        """
        Finish logging request.

        @param log_request: Logger instace.
        @param response_id: Response ID. It can be None. None causes the request result is 'Fail'.
        @param error_object: Error object of python exception or corba exception.
        """
        if log_request is None:
            return
        properties_out, references = [], []
        if error_object:
            if isinstance(error_object, PublicRequestKnownException):
                properties_out.append(("reason", error_object.exception_code_name))
                log_request.result = "Fail"
            else:
                # Default result is "Error"
                properties_out.append(("exception", error_object.__class__.__name__))
        else:
            if response_id:
                references.append(('publicrequest', response_id))
                log_request.result = "Ok"
            else:
                log_request.result = "Fail"
        log_request.close(properties=properties_out, references=references)


class PublicRequestFormView(PublicRequestLoggerMixin, FormView):
    """FormView for manage public requests. Logs calls to the registry if LOGGER is set."""

    public_key = None  # public key for the cache key with a response values.

    def _get_object_type(self, name):
        return {
            'domain': REGISTRY_MODULE.PublicRequest.ObjectType_PR.domain,
            'contact': REGISTRY_MODULE.PublicRequest.ObjectType_PR.contact,
            'nsset': REGISTRY_MODULE.PublicRequest.ObjectType_PR.nsset,
            'keyset': REGISTRY_MODULE.PublicRequest.ObjectType_PR.keyset
        }[name]

    def _get_confirmed_by_type(self, name):
        return {
            'signed_email': REGISTRY_MODULE.PublicRequest.ConfirmedBy.signed_email,
            'notarized_letter': REGISTRY_MODULE.PublicRequest.ConfirmedBy.notarized_letter,
        }[name]

    def _call_registry_command(self, form, log_request_id):
        """Call a registry command. Return response_id or raise exception if the call failed."""
        raise NotImplementedError

    def set_to_cache(self, data):
        """Set values into the cache."""
        cache.set(self.public_key, data, 60 * 60 * 24)

    def logged_call_to_registry(self, form):
        """
         Log the call to the registry.

        @param form: Django form instance with cleaned_data.
        @return: Response ID.
        """
        self.public_key = get_random_string(64)
        cached_data = {}
        cached_data.update(form.cleaned_data)
        if LOGGER:
            log_request = self.prepare_logging_request(form.cleaned_data)
            log_request_id = log_request.request_id
            cached_data['request_name'] = log_request.request_type
        else:
            log_request = log_request_id = None
        response_id = err = None
        try:
            cached_data['response_id'] = response_id = self._call_registry_command(form, log_request_id)
            cached_data['created_date'] = timezone_now().date()
            self.set_to_cache(cached_data)
        except BaseException as err:
            raise
        finally:
            self.finish_logging_request(log_request, response_id, err)

    def form_valid(self, form):
        try:
            self.logged_call_to_registry(form)
        except PublicRequestKnownException:
            return self.form_invalid(form)
        self.form_cleaned_data = form.cleaned_data
        return super(PublicRequestFormView, self).form_valid(form)
