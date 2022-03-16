#
# Copyright (C) 2015-2022  CZ.NIC, z. s. p. o.
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
from contextlib import suppress
from typing import Any, Dict

import idna
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from fred_idl.Registry.Whois import (INVALID_HANDLE, INVALID_LABEL, OBJECT_DELETE_CANDIDATE, OBJECT_NOT_FOUND,
                                     TOO_MANY_LABELS, UNMANAGED_ZONE)

from webwhois.utils import WHOIS
from webwhois.views import ContactDetailMixin, DomainDetailMixin, KeysetDetailMixin, NssetDetailMixin
from webwhois.views.base import RegistryObjectMixin
from webwhois.views.registrar import RegistrarDetailMixin

from ..context_processors import _get_managed_zones
from ..exceptions import WebwhoisError
from ..utils.deprecation import deprecated_context


class ResolveHandleTypeMixin(RegistryObjectMixin):
    """Find all objects with the handle."""

    multiple_entries_template = "webwhois/multiple_entries.html"
    object_type_name = "multiple"

    @classmethod
    def load_registry_object(cls, context, handle):
        """Load all registry objects of the handle and append it into the context."""
        # Ignore errors from object search.
        with suppress(WebwhoisError):
            ContactDetailMixin.load_registry_object(context, handle)
        with suppress(WebwhoisError):
            NssetDetailMixin.load_registry_object(context, handle)
        with suppress(WebwhoisError):
            KeysetDetailMixin.load_registry_object(context, handle)
        with suppress(WebwhoisError):
            RegistrarDetailMixin.load_registry_object(context, handle)
        with suppress(WebwhoisError):
            DomainDetailMixin.load_registry_object(context, handle)

        if not context[cls._registry_objects_key]:
            # No object was found. Create a virtual server exception to render its template.
            # TODO: This solution is hopefully temporary and should be removed very soon.
            context["server_exception"] = WebwhoisError(
                code="OBJECT_NOT_FOUND",
                title=_("Record not found"),
                message=cls.message_with_handle_in_html(_("%s does not match any record."), handle),
                object_not_found=True,
            )
            context["managed_zone_list"] = deprecated_context(
                _get_managed_zones(),
                "Context variable 'managed_zone_list' is deprecated. Use 'managed_zones' context processor instead.")

    def load_related_objects(self, context):
        """Prepare url for redirect to the registry object type."""
        registry_object_type = list(context[self._registry_objects_key].keys())[0]
        url = reverse("webwhois:detail_%s" % registry_object_type, kwargs={"handle": self.kwargs["handle"]},
                      current_app=self.request.resolver_match.namespace)
        context.setdefault("redirect_to_type", url)

    def _get_object(self, handle: str) -> Any:
        objects = {}
        with suppress(OBJECT_NOT_FOUND, INVALID_HANDLE):
            objects['contact'] = WHOIS.get_contact_by_handle(handle)
        with suppress(OBJECT_NOT_FOUND, INVALID_HANDLE):
            objects['nsset'] = WHOIS.get_nsset_by_handle(handle)
        with suppress(OBJECT_NOT_FOUND, INVALID_HANDLE):
            objects['keyset'] = WHOIS.get_keyset_by_handle(handle)
        with suppress(OBJECT_NOT_FOUND, INVALID_HANDLE):
            objects['registrar'] = WHOIS.get_registrar_by_handle(handle)
        if not handle.startswith("."):
            with suppress(OBJECT_NOT_FOUND, UNMANAGED_ZONE, INVALID_LABEL, TOO_MANY_LABELS, idna.IDNAError):
                idna_handle = idna.encode(handle).decode()
                try:
                    objects['domain'] = WHOIS.get_domain_by_handle(idna_handle)
                except OBJECT_DELETE_CANDIDATE:
                    objects['domain'] = None
        if not objects:
            raise WebwhoisError(
                code="OBJECT_NOT_FOUND",
                title=_("Record not found"),
                message=self.message_with_handle_in_html(_("%s does not match any record."), handle),
                object_not_found=True,
            )
        return objects

    def _make_context(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Turn object into a context."""
        return {k: {'detail': v} for k, v in obj.items()}

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if "redirect_to_type" in context:
            return HttpResponseRedirect(context["redirect_to_type"])
        return super(ResolveHandleTypeMixin, self).get(request, *args, **kwargs)

    def get_context_data(self, handle, **kwargs):
        context = super().get_context_data(handle, **kwargs)
        if ('managed_zone_list' not in context
                and getattr(context.get('server_exception'), 'code', None) == 'OBJECT_NOT_FOUND'):
            context["managed_zone_list"] = deprecated_context(
                _get_managed_zones(),
                "Context variable 'managed_zone_list' is deprecated. Use 'managed_zones' context processor instead.")
        return context

    def get_template_names(self):
        context = self._get_registry_objects()
        if len(context[self._registry_objects_key]) > 1:
            return [self.multiple_entries_template]
        return super(ResolveHandleTypeMixin, self).get_template_names()


class ResolveHandleTypeView(ResolveHandleTypeMixin, TemplateView):
    """View which searches all types of objects."""
