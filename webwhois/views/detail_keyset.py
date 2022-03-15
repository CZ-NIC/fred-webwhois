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
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from fred_idl.Registry.Whois import INVALID_HANDLE, OBJECT_NOT_FOUND

from webwhois.utils import WHOIS
from webwhois.views.base import RegistryObjectMixin

from ..exceptions import WebwhoisError


class KeysetDetailMixin(RegistryObjectMixin):

    template_name = "webwhois/keyset.html"
    object_type_name = "keyset"

    @classmethod
    def append_keyset_related(cls, data):
        """Load objects related to the nsset and append them into the data context."""
        descriptions = cls._get_status_descriptions("keyset", WHOIS.get_keyset_status_descriptions)
        registry_object = data["detail"]
        data.update({
            "admins": [WHOIS.get_contact_by_handle(handle) for handle in registry_object.tech_contact_handles],
            "registrar": WHOIS.get_registrar_by_handle(registry_object.registrar_handle),
            "status_descriptions": [descriptions[key] for key in registry_object.statuses],
        })

    @classmethod
    def load_registry_object(cls, context, handle):
        """Load keyset of the handle and append it into the context."""
        try:
            context[cls._registry_objects_key]["keyset"] = {
                "detail": WHOIS.get_keyset_by_handle(handle),
                "label": _("Keyset"),
            }
        except OBJECT_NOT_FOUND as error:
            raise WebwhoisError(
                'OBJECT_NOT_FOUND',
                title=_("Key server set not found"),
                message=cls.message_with_handle_in_html(_("No key set matches %s handle."), handle),
            ) from error
        except INVALID_HANDLE as error:
            raise WebwhoisError(**cls.message_invalid_handle(handle)) from error

    def load_related_objects(self, context):
        """Load objects related to the keyset and append them into the context."""
        self.append_keyset_related(context[self._registry_objects_key]["keyset"])


class KeysetDetailView(KeysetDetailMixin, TemplateView):
    """View with details of a keyset."""
