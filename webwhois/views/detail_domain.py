#
# Copyright (C) 2015-2018  CZ.NIC, z. s. p. o.
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

from __future__ import unicode_literals

import re

import idna
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from fred_idl.Registry.Whois import INVALID_LABEL, OBJECT_DELETE_CANDIDATE, OBJECT_NOT_FOUND, TOO_MANY_LABELS, \
    UNMANAGED_ZONE

from webwhois.constants import STATUS_DELETE_CANDIDATE
from webwhois.settings import WEBWHOIS_DNSSEC_URL
from webwhois.utils import WHOIS
from webwhois.views import KeysetDetailMixin, NssetDetailMixin
from webwhois.views.base import RegistryObjectMixin


class DomainDetailMixin(RegistryObjectMixin):

    template_name = "webwhois/domain.html"
    object_type_name = "domain"

    @classmethod
    def make_message_not_found(cls, handle, handle_is_domain):
        """Handle or domain not found."""
        if handle_is_domain:
            title = _("Domain not found")
            message = _("No domain matches %s handle.")
        else:
            title = _("Handle not found")
            message = _("No domain, contact or name server set matches %s query.")
        return {
            "title": title,
            "message": cls.message_with_handle_in_html(message, handle)
        }

    @classmethod
    def load_registry_object(cls, context, handle, handle_is_domain=True):
        """
        Load domain of the handle and append it into the context.

        Param 'handle_is_domain' has an impact on error message.
        """
        if handle.startswith("."):
            context["server_exception"] = cls.message_invalid_handle(handle)
            return

        try:
            idna_handle = idna.encode(handle).decode()
        except idna.IDNAError:
            if handle_is_domain:
                context["server_exception"] = cls.message_invalid_handle(handle, "IDNAError")
            else:
                context["server_exception"] = {
                    "code": "IDNAError",
                    "title": _("Handle not found"),
                    "message": cls.message_with_handle_in_html(
                        _("No domain, contact or name server set matches %s query."), handle)
                }
            return

        try:
            context[cls._registry_objects_key]["domain"] = {
                "detail": WHOIS.get_domain_by_handle(idna_handle),
                "label": _("Domain"),
            }
        except OBJECT_DELETE_CANDIDATE:
            context['object_delete_candidate'] = True
            # Add fake domain into context for ResolveHandleTypeMixin.
            context[cls._registry_objects_key]['domain'] = None
        except OBJECT_NOT_FOUND:
            # Only handle with format of valid domain name and in managed zone raises OBJECT_NOT_FOUND.
            context["server_exception"] = cls.make_message_not_found(handle, handle_is_domain)
            context["server_exception"]["handle_is_in_zone"] = True
        except UNMANAGED_ZONE:
            if handle_is_domain:
                context["managed_zone_list"] = WHOIS.get_managed_zone_list()
                context["server_exception"] = {
                    "code": "UNMANAGED_ZONE",
                    "title": _("Unmanaged zone"),
                    "message": cls.message_with_handle_in_html(
                        _("Domain %s cannot be found in the registry. "
                          "You can search for domains in the these zones only:"), handle),
                    "unmanaged_zone": True,
                }
            else:
                # It is a search for any type of object and the handle isn't a domain. Act as if the object isn't found.
                context["server_exception"] = cls.make_message_not_found(handle, handle_is_domain)
        except INVALID_LABEL:
            # Pattern for the handle is more vague than the pattern of domain name format.
            context["server_exception"] = cls.message_invalid_handle(handle, "INVALID_LABEL")
        except TOO_MANY_LABELS:
            # Caution! Domain name can have more than one fullstop character and it is still valid.
            # for example: '0.2.4.e164.arpa'
            # remove subdomain names: 'www.sub.domain.cz' -> 'domain.cz'
            context["example_domain_name"] = re.search(r"([^.]+\.\w+)\.?$", handle, re.IGNORECASE).group(1)
            context["server_exception"] = {
                "code": "TOO_MANY_LABELS",
                "title": _("Incorrect input"),
                "too_many_parts_in_domain_name": True,
            }

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

    def get_context_data(self, **kwargs):
        kwargs.setdefault("DNSSEC_URL", WEBWHOIS_DNSSEC_URL)
        return super(DomainDetailMixin, self).get_context_data(**kwargs)


class DomainDetailView(DomainDetailMixin, TemplateView):
    """View with details of a domain."""
