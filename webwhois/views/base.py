from django.core.cache import cache
from django.utils import six  # Python 3 compatibility
from django.utils.encoding import force_bytes
from django.utils.functional import lazy
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, ugettext_lazy as _
from django.views.generic.base import ContextMixin

mark_safe_lazy = lazy(mark_safe, six.text_type)


class BaseContextMixin(ContextMixin):
    """
    Set 'webwhois_base_template' into the context.
    """

    webwhois_base_template = "webwhois_in_cms/main_in_content.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("webwhois_base_template", self.webwhois_base_template)
        return super(BaseContextMixin, self).get_context_data(**kwargs)

    def render_to_response(self, context, **response_kwargs):
        response_kwargs['current_app'] = self.request.resolver_match.namespace
        return super(BaseContextMixin, self).render_to_response(context, **response_kwargs)


class RegistryObjectMixin(BaseContextMixin):
    """
    Base class for loading object registry of the handle.

    It is rasied standard HTTP 500 "Server Error" page when Corba backend falied.
    Catch omniORB.CORBA.TRANSIENT and omniORB.CORBA.OBJECT_NOT_EXIST
    and redirect to your own customized page if you need.
    """
    _WHOIS = None
    _LOGGER = None
    _registry_objects_key = "registry_objects"
    _registry_objects_cache = None

    server_exception_template = "webwhois/server_exception.html"
    object_type_name = None

    @staticmethod
    def _get_status_descriptions(type_name, fnc_get_descriptions):
        """
        Get status descritions from the cache. Load them from a backend and put in the cache if they missing there.

        Load status only for a defined object type and current site language.
        """
        lang = get_language()
        cache_key = "webwhois_descr_%s_%s" % (lang, type_name)
        descripts = cache.get(cache_key)
        if not descripts:
            # Registry.Whois.ObjectStatusDesc(handle='serverDeleteProhibited', name='Deletion forbidden')
            descripts = {object_status_desc.handle: object_status_desc.name
                         for object_status_desc in fnc_get_descriptions(force_bytes(lang))}
            cache.set(cache_key, descripts)
        return descripts

    @staticmethod
    def message_with_handle_in_html(text, handle):
        "Make html message and mark it safe."
        return mark_safe_lazy(text % "<strong>%s</strong>" % escape(handle))

    @classmethod
    def message_invalid_handle(cls, handle, code="INVALID_HANDLE"):
        return {
            "code": code,
            "title": _("Invalid handle"),
            "message": cls.message_with_handle_in_html(_("%s is not a valid handle."), handle),
        }

    @classmethod
    def load_registry_object(cls, context, handle, backend):
        "Load registry object of the handle and append it into the context."

    def load_related_objects(self, context):
        "Load objects related to the main registry object and append them into the context."

    def prepare_logging_request(self):
        if self.object_type_name is None:
            raise NotImplementedError
        if not self._LOGGER:
            return
        properties_in = (
            ("handle", self.kwargs["handle"]),
            ("handleType", self.object_type_name),
        )
        return self._LOGGER.create_request(self.request.META.get('REMOTE_ADDR', ''), "Web whois", "Info",
                                           properties=properties_in)

    def finish_logging_request(self, log_request, context, exception_type_name=None):
        if log_request is None:
            return
        properties_out = []
        if exception_type_name is not None:
            log_request.result = "Error"
            properties_out.append(("exception", exception_type_name))
        else:
            found_types = [("foundType", name) for name in context.get(self._registry_objects_key, {}).keys()]
            if len(found_types):
                log_request.result = "Ok"
                properties_out.extend(found_types)
            else:
                log_request.result = "NotFound"
                exception_code = context.get("server_exception", {}).get("code")
                if exception_code and exception_code != "OBJECT_NOT_FOUND":
                    properties_out.append(("reason", exception_code))
        log_request.close(properties=properties_out)

    def _get_registry_objects(self):
        "The function returns a dict with objects loaded from the registry."
        if self._registry_objects_cache is None:
            context = {self._registry_objects_key: {}}
            log_request = self.prepare_logging_request()
            exception_name = None
            try:
                self.load_registry_object(context, self.kwargs["handle"], self._WHOIS)
            except BaseException as err:
                exception_name = err.__class__.__name__
                raise
            finally:
                self.finish_logging_request(log_request, context, exception_name)
            if len(context[self._registry_objects_key]) == 1:
                self.load_related_objects(context)
            self._registry_objects_cache = context
        return self._registry_objects_cache

    def get_context_data(self, handle, **kwargs):
        kwargs.setdefault("handle", handle)
        kwargs.update(self._get_registry_objects())
        kwargs["number_of_found_objects"] = len(kwargs[self._registry_objects_key])
        if "template_name" in kwargs:
            self.template_name = kwargs["template_name"]
        elif "server_exception" in kwargs:
            self.template_name = self.server_exception_template
        return super(RegistryObjectMixin, self).get_context_data(**kwargs)
