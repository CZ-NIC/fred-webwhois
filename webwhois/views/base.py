from django.core.cache import cache
from django.utils import six  # Python 3 compatibility
from django.utils.encoding import force_bytes
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, ugettext_lazy as _
from django.views.generic.base import ContextMixin

mark_safe_lazy = lazy(mark_safe, six.text_type)


class BaseContextMixin(ContextMixin):
    """
    Set 'webwhois_base_template' into the context.

    Creates url names with namespace from 'urls_namespace' and set them into the context.
    """

    webwhois_base_template = "webwhois_in_cms/main_in_content.html"
    urls_namespace = "webwhois"

    def add_ns(self, name):
        return "%s:%s" % (self.urls_namespace, name)

    def _url_names_with_namespace(self):
        return "webwhois", {
            "form_whois": self.add_ns("form_whois"),
            "download": {
                "evaluation_file": self.add_ns("download_evaluation_file")
            },
            "detail": {
                "contact": self.add_ns("detail_contact"),
                "nsset": self.add_ns("detail_nsset"),
                "keyset": self.add_ns("detail_keyset"),
                "domain": self.add_ns("detail_domain"),
                "registrar": self.add_ns("detail_registrar"),
            },
            "registrar": {
                "list_retail": self.add_ns("registrar_list_retail"),
            }
        }

    def get_context_data(self, **kwargs):
        kwargs.setdefault("webwhois_base_template", self.webwhois_base_template)
        kwargs.setdefault(*self._url_names_with_namespace())
        return super(BaseContextMixin, self).get_context_data(**kwargs)


class RegistryObjectMixin(BaseContextMixin):
    """
    Base class for loading object registry of the handle.

    It is rasied standard HTTP 500 "Server Error" page when Corba backend falied.
    Catch omniORB.CORBA.TRANSIENT and omniORB.CORBA.OBJECT_NOT_EXIST
    and redirect to your own customized page if you need.
    """
    _CORBA = None
    _WHOIS = None
    _registry_objects_key = "registry_objects"

    server_exception_template = "webwhois/server_exception.html"

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
        return mark_safe_lazy(text % "<strong>%s</strong>" % handle)

    @classmethod
    def message_invalid_handle(cls, handle):
        return {
            "title": _("Invalid handle"),
            "message": cls.message_with_handle_in_html(_("%s is not a valid handle."), handle),
        }

    @classmethod
    def load_registry_object(cls, context, handle, backend):
        "Load registry object of the handle and append it into the context."

    def load_related_objects(self, context):
        "Load objects related to the main registry object and append them into the context."

    def get_context_data(self, handle, **kwargs):
        kwargs.setdefault("handle", handle)
        kwargs.setdefault(self._registry_objects_key, {})
        kwargs.setdefault(*self._url_names_with_namespace())
        self.load_registry_object(kwargs, handle, (self._CORBA, self._WHOIS))
        kwargs["number_of_found_objects"] = len(kwargs[self._registry_objects_key])
        if kwargs["number_of_found_objects"] == 1:
            self.load_related_objects(kwargs)
        elif "template_name" in kwargs:
            self.template_name = kwargs["template_name"]
        elif "server_exception" in kwargs:
            self.template_name = self.server_exception_template
        return super(RegistryObjectMixin, self).get_context_data(**kwargs)
