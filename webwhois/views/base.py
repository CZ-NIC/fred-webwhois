#
# Copyright (C) 2015-2020  CZ.NIC, z. s. p. o.
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
from django.core.cache import cache
from django.utils.functional import lazy
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, ugettext_lazy as _
from django.views.generic.base import ContextMixin

from webwhois.constants import STATUS_DELETE_CANDIDATE
from webwhois.utils import LOGGER

mark_safe_lazy = lazy(mark_safe, str)


class BaseContextMixin(ContextMixin):
    """Base mixin for webwhois views.

    @cvar base_template: Path to base template.
    """

    base_template = "base_site_example.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("base_template", self.base_template)
        return super(BaseContextMixin, self).get_context_data(**kwargs)

    def render_to_response(self, context, **response_kwargs):
        self.request.current_app = self.request.resolver_match.namespace
        return super(BaseContextMixin, self).render_to_response(context, **response_kwargs)


class RegistryObjectMixin(BaseContextMixin):
    """
    Base class for loading object registry of the handle.

    It is rasied standard HTTP 500 "Server Error" page when Corba backend falied.
    Catch omniORB.CORBA.TRANSIENT and omniORB.CORBA.OBJECT_NOT_EXIST
    and redirect to your own customized page if you need.
    """

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
            descripts = {object_status_desc.handle: object_status_desc.name
                         for object_status_desc in fnc_get_descriptions(lang)}
            cache.set(cache_key, descripts)
        return descripts

    @staticmethod
    def message_with_handle_in_html(text, handle):
        """Make html message and mark it safe."""
        return mark_safe_lazy(text % "<strong>%s</strong>" % escape(handle))

    @classmethod
    def message_invalid_handle(cls, handle, code="INVALID_HANDLE"):
        return {
            "code": code,
            "title": _("Invalid handle"),
            "message": cls.message_with_handle_in_html(_("%s is not a valid handle."), handle),
        }

    @classmethod
    def load_registry_object(cls, context, handle):
        """Load registry object of the handle and append it into the context."""

    def load_related_objects(self, context):
        """Load objects related to the main registry object and append them into the context."""

    def prepare_logging_request(self):
        if self.object_type_name is None:
            raise NotImplementedError
        if not LOGGER:
            return
        properties_in = (
            ("handle", self.kwargs["handle"]),
            ("handleType", self.object_type_name),
        )
        return LOGGER.create_request(self.request.META.get('REMOTE_ADDR', ''), "Web whois", "Info",
                                     properties=properties_in)

    def finish_logging_request(self, log_request, context, exception_type_name=None):
        if log_request is None:
            return
        properties_out = []
        if exception_type_name is not None:
            log_request.result = "Error"
            properties_out.append(("exception", exception_type_name))
        else:
            found_types = [("foundType", name) for name in sorted(context.get(self._registry_objects_key, {}).keys())]
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
        """Return a dict with objects loaded from the registry."""
        if self._registry_objects_cache is None:
            context = {self._registry_objects_key: {}}
            log_request = self.prepare_logging_request()
            exception_name = None
            try:
                self.load_registry_object(context, self.kwargs["handle"])
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
        objects = self._get_registry_objects()
        kwargs.update(objects)
        if self.object_type_name in objects[self._registry_objects_key]:
            obj = objects[self._registry_objects_key][self.object_type_name]
            # `obj` may be None, if domain is a delete candidate.
            if obj is not None:
                # Registrars don't have statuses
                kwargs['object_delete_candidate'] = STATUS_DELETE_CANDIDATE in getattr(obj['detail'], 'statuses', ())
        return super(RegistryObjectMixin, self).get_context_data(**kwargs)

    def get_template_names(self):
        context = self._get_registry_objects()
        if "server_exception" in context:
            return [self.server_exception_template]
        return super(RegistryObjectMixin, self).get_template_names()
