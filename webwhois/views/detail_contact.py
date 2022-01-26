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
import datetime

from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from fred_idl.Registry.Whois import INVALID_HANDLE, OBJECT_NOT_FOUND

from webwhois.constants import (STATUS_CONDITIONALLY_IDENTIFIED, STATUS_IDENTIFIED, STATUS_LINKED, STATUS_VALIDATED,
                                STATUS_VERIFICATION_FAILED, STATUS_VERIFICATION_IN_PROCESS, STATUS_VERIFICATION_PASSED)
from webwhois.utils import WHOIS
from webwhois.views.base import RegistryObjectMixin


class ContactDetailMixin(RegistryObjectMixin):

    template_name = "webwhois/contact.html"
    object_type_name = "contact"

    CONTACT_VERIFICATION_STATUS = (STATUS_VERIFICATION_IN_PROCESS, STATUS_VERIFICATION_PASSED,
                                   STATUS_VERIFICATION_FAILED, STATUS_CONDITIONALLY_IDENTIFIED, STATUS_IDENTIFIED,
                                   STATUS_VALIDATED)
    ICON_PATH = "webwhois/img/"
    VERIFICATION_STATUS_ICON = {
        STATUS_VERIFICATION_IN_PROCESS: ICON_PATH + "icon-orange-cross.gif",
        STATUS_VERIFICATION_FAILED: ICON_PATH + "icon-red-cross.gif",
        "DEFAULT": ICON_PATH + "icon-yes.gif",
    }

    @classmethod
    def load_registry_object(cls, context, handle):
        """Load contact of the handle and append it into the context."""
        try:
            contact = WHOIS.get_contact_by_handle(handle)
            birthday = None
            if contact.identification.value.identification_type == "BIRTHDAY":
                try:
                    birthday = datetime.datetime.strptime(contact.identification.value.identification_data,
                                                          '%Y-%m-%d').date()
                except ValueError:
                    birthday = contact.identification.value.identification_data
            context[cls._registry_objects_key]["contact"] = {
                "detail": contact,
                "birthday": birthday,
                "label": _("Contact"),
            }
        except OBJECT_NOT_FOUND:
            context["server_exception"] = {
                "title": _("Contact not found"),
                "message": cls.message_with_handle_in_html(_("No contact matches %s handle."), handle),
            }
        except INVALID_HANDLE:
            context["server_exception"] = cls.message_invalid_handle(handle)

    def load_related_objects(self, context):
        """Load objects related to the contact and append them into the context."""
        descriptions = self._get_status_descriptions("contact", WHOIS.get_contact_status_descriptions)
        data = context[self._registry_objects_key]["contact"]  # detail, type, label, href
        registry_object = data["detail"]

        ver_status = [{"code": key, "label": descriptions[key],
                       "icon": self.VERIFICATION_STATUS_ICON.get(key, self.VERIFICATION_STATUS_ICON["DEFAULT"])}
                      for key in registry_object.statuses if key in self.CONTACT_VERIFICATION_STATUS]
        data.update({
            "status_descriptions": [descriptions[key] for key in registry_object.statuses
                                    if key not in self.CONTACT_VERIFICATION_STATUS],
            "verification_status": ver_status,
            "is_linked": STATUS_LINKED in registry_object.statuses
        })
        if registry_object.creating_registrar_handle:
            data["creating_registrar"] = WHOIS.get_registrar_by_handle(registry_object.creating_registrar_handle)
        if registry_object.sponsoring_registrar_handle:
            data["sponsoring_registrar"] = WHOIS.get_registrar_by_handle(registry_object.sponsoring_registrar_handle)


class ContactDetailView(ContactDetailMixin, TemplateView):
    """View with details of a contact."""
