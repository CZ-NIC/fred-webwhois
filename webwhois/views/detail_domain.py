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
import re
from typing import Any, Dict, cast

import idna
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from fred_idl.Registry.Whois import (INVALID_LABEL, OBJECT_DELETE_CANDIDATE, OBJECT_NOT_FOUND, TOO_MANY_LABELS,
                                     UNMANAGED_ZONE, Domain)

from webwhois.constants import STATUS_DELETE_CANDIDATE
from webwhois.utils import WHOIS
from webwhois.utils.cdnskey_client import get_cdnskey_client
from webwhois.views import KeysetDetailMixin, NssetDetailMixin
from webwhois.views.base import RegistryObjectMixin

from ..context_processors import _get_managed_zones
from ..exceptions import WebwhoisError
from ..utils.deprecation import deprecated_context


class DomainDetailMixin(RegistryObjectMixin):

    template_name = "webwhois/domain.html"
    object_type_name = "domain"

    @classmethod
    def make_message_not_found(cls, handle):
        """Handle or domain not found."""
        title = _("Domain not found")
        message = _("No domain matches %s handle.")
        return {
            "title": title,
            "message": cls.message_with_handle_in_html(message, handle)
        }

    @classmethod
    def load_registry_object(cls, context, handle):
        """Load domain of the handle and append it into the context."""
        if handle.startswith("."):
            raise WebwhoisError(**cls.message_invalid_handle(handle))

        try:
            idna_handle = idna.encode(handle).decode()
        except idna.IDNAError:
            raise WebwhoisError(**cls.message_invalid_handle(handle, "IDNAError"))

        try:
            context[cls._registry_objects_key]["domain"] = {
                "detail": WHOIS.get_domain_by_handle(idna_handle),
                "label": _("Domain"),
            }
        except OBJECT_DELETE_CANDIDATE:
            context['object_delete_candidate'] = True
            # Add fake domain into context for ResolveHandleTypeMixin.
            context[cls._registry_objects_key]['domain'] = None
        except OBJECT_NOT_FOUND as error:
            # Only handle with format of valid domain name and in managed zone raises OBJECT_NOT_FOUND.
            raise WebwhoisError('OBJECT_NOT_FOUND', **cls.make_message_not_found(handle),
                                handle_is_in_zone=True) from error
        except UNMANAGED_ZONE as error:
            context["managed_zone_list"] = deprecated_context(
                _get_managed_zones(),
                "Context variable 'managed_zone_list' is deprecated. Use 'managed_zones' context processor instead.")
            message = cls.message_with_handle_in_html(
                _("Domain %s cannot be found in the registry. You can search for domains in the these zones only:"),
                handle)
            raise WebwhoisError('UNMANAGED_ZONE', title=_("Unmanaged zone"), message=message,
                                unmanaged_zone=True) from error
        except INVALID_LABEL:
            # Pattern for the handle is more vague than the pattern of domain name format.
            raise WebwhoisError(**cls.message_invalid_handle(handle, "INVALID_LABEL"))
        except TOO_MANY_LABELS as error:
            # Caution! Domain name can have more than one fullstop character and it is still valid.
            # for example: '0.2.4.e164.arpa'
            # remove subdomain names: 'www.sub.domain.cz' -> 'domain.cz'
            domain_match = re.search(r"([^.]+\.\w+)\.?$", handle, re.IGNORECASE)
            assert domain_match is not None
            context["example_domain_name"] = domain_match.group(1)
            raise WebwhoisError('TOO_MANY_LABELS', title=_("Incorrect input"),
                                # Templates in webwhois <=1.20 didn't expect message to be `None`.
                                message='',
                                too_many_parts_in_domain_name=True) from error

    def _get_object(self, handle: str) -> Domain:
        if handle.startswith("."):
            raise WebwhoisError(**self.message_invalid_handle(handle))

        try:
            idna_handle = idna.encode(handle).decode()
        except idna.IDNAError:
            raise WebwhoisError(**self.message_invalid_handle(handle, "IDNAError"))

        try:
            return WHOIS.get_domain_by_handle(idna_handle)
        except OBJECT_DELETE_CANDIDATE:
            return Domain(handle, None, (), None, None, None, ['deleteCandidate'], None, None, None, None, None, None,
                          None, None, None)
        except OBJECT_NOT_FOUND as error:
            # Only handle with format of valid domain name and in managed zone raises OBJECT_NOT_FOUND.
            raise WebwhoisError('OBJECT_NOT_FOUND', **self.make_message_not_found(handle),
                                handle_is_in_zone=True) from error
        except UNMANAGED_ZONE as error:
            message = self.message_with_handle_in_html(
                _("Domain %s cannot be found in the registry. You can search for domains in the these zones only:"),
                handle)
            raise WebwhoisError('UNMANAGED_ZONE', title=_("Unmanaged zone"), message=message,
                                unmanaged_zone=True) from error
        except INVALID_LABEL as error:
            # Pattern for the handle is more vague than the pattern of domain name format.
            raise WebwhoisError(**self.message_invalid_handle(handle, "INVALID_LABEL")) from error
        except TOO_MANY_LABELS as error:
            raise WebwhoisError('TOO_MANY_LABELS', title=_("Incorrect input"),
                                # Templates in webwhois <=1.20 didn't expect message to be `None`.
                                message='',
                                too_many_parts_in_domain_name=True) from error

    def _make_context(self, obj: Any) -> Dict[str, Any]:
        """Turn object into a context."""
        context = super()._make_context(obj)
        context[self.object_type_name]["label"] = _("Domain")
        return context

    def get_context_data(self, handle, **kwargs):
        context = super().get_context_data(handle, **kwargs)
        if ('managed_zone_list' not in context
                and getattr(context.get('server_exception'), 'code', None) == 'UNMANAGED_ZONE'):
            context["managed_zone_list"] = deprecated_context(
                _get_managed_zones(),
                "Context variable 'managed_zone_list' is deprecated. Use 'managed_zones' context processor instead.")
        if ('example_domain_name' not in context
                and getattr(context.get('server_exception'), 'code', None) == 'TOO_MANY_LABELS'):
            # Caution! Domain name can have more than one fullstop character and it is still valid.
            # for example: '0.2.4.e164.arpa'
            # remove subdomain names: 'www.sub.domain.cz' -> 'domain.cz'
            domain_match = re.search(r"([^.]+\.\w+)\.?$", handle, re.IGNORECASE)
            if domain_match:
                context["example_domain_name"] = domain_match.group(1)
        return context

    def load_related_objects(self, context):
        """Load objects related to the domain and append them into the context."""
        descriptions = self._get_status_descriptions("domain", WHOIS.get_domain_status_descriptions)
        data = context[self._registry_objects_key]["domain"]  # detail, type, label, href
        if data is None:
            # Domain is a delete candidate
            return
        registry_object = data["detail"]
        data["status_descriptions"] = [descriptions[key] for key in registry_object.statuses]
        if STATUS_DELETE_CANDIDATE in registry_object.statuses:
            return
        data.update({
            "registrant": WHOIS.get_contact_by_handle(registry_object.registrant_handle),
            "registrar": WHOIS.get_registrar_by_handle(registry_object.registrar_handle),
            "admins": [WHOIS.get_contact_by_handle(handle) for handle in registry_object.admin_contact_handles],
        })
        if registry_object.nsset_handle:
            data["nsset"] = {"detail": WHOIS.get_nsset_by_handle(registry_object.nsset_handle)}
            NssetDetailMixin.append_nsset_related(data["nsset"])
        if registry_object.keyset_handle:
            data["keyset"] = {"detail": WHOIS.get_keyset_by_handle(registry_object.keyset_handle)}
            KeysetDetailMixin.append_keyset_related(data["keyset"])


class DomainDetailView(DomainDetailMixin, TemplateView):
    """View with details of a domain."""

    def get_context_data(self, handle: str, **kwargs) -> Dict:  # type: ignore[override]
        context = cast(Dict, super().get_context_data(handle=handle, **kwargs))
        if get_cdnskey_client() is not None:
            context['scan_results_link'] = reverse('webwhois:scan_results', kwargs={'handle': handle})
        return context
