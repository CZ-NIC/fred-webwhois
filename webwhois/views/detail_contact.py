import datetime
import re

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from webwhois.utils import WHOIS_MODULE
from webwhois.views.base import RegistryObjectMixin


class ContactDetailMixin(RegistryObjectMixin):

    template_name = "webwhois/contact.html"
    object_type_name = "contact"

    CONTACT_VERIFICATION_STATUS = (
        'conditionallyIdentifiedContact',
        'contactFailedManualVerification',
        'contactInManualVerification',
        'contactPassedManualVerification',
        'identifiedContact',
        'validatedContact',
    )
    ICON_PATH = "webwhois/img/"
    VERIFICATION_STATUS_ICON = {
        "contactInManualVerification": ICON_PATH + "icon-orange-cross.gif",
        "contactFailedManualVerification": ICON_PATH + "icon-red-cross.gif",
        "DEFAULT": ICON_PATH + "icon-yes.gif",
    }

    @classmethod
    def load_registry_object(cls, context, handle, backend):
        "Load contact of the handle and append it into the context."
        try:
            contact = backend.get_contact_by_handle(handle)
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
        except WHOIS_MODULE.OBJECT_NOT_FOUND:
            context["server_exception"] = {
                "title": _("Contact not found"),
                "message": cls.message_with_handle_in_html(_("No contact matches %s handle."), handle),
            }
        except WHOIS_MODULE.INVALID_HANDLE:
            context["server_exception"] = cls.message_invalid_handle(handle)

    def load_related_objects(self, context):
        "Load objects related to the contact and append them into the context."
        descriptions = self._get_status_descriptions("contact", self._WHOIS.get_contact_status_descriptions)
        data = context[self._registry_objects_key]["contact"]  # detail, type, label, href
        registry_object = data["detail"]

        ver_status = [{"code": key, "label": descriptions[key],
                       "icon": self.VERIFICATION_STATUS_ICON.get(key, self.VERIFICATION_STATUS_ICON["DEFAULT"])}
                      for key in registry_object.statuses if key in self.CONTACT_VERIFICATION_STATUS]
        data.update({
            "status_descriptions": [descriptions[key] for key in registry_object.statuses
                                    if key not in self.CONTACT_VERIFICATION_STATUS],
            "verification_status": ver_status,
            "is_linked": "linked" in registry_object.statuses
        })
        if registry_object.creating_registrar_handle:
            data["creating_registrar"] = self._WHOIS.get_registrar_by_handle(
                registry_object.creating_registrar_handle)
        if registry_object.sponsoring_registrar_handle:
            data["sponsoring_registrar"] = self._WHOIS.get_registrar_by_handle(
                registry_object.sponsoring_registrar_handle)


class ContactDetailWithMojeidMixin(ContactDetailMixin):

    template_name = "webwhois_in_cms/contact_with_mojeid.html"
    valid_mojeid_handle_format = re.compile('^[A-Z0-9](-?[A-Z0-9])*$', re.IGNORECASE)

    def get_context_data(self, **kwargs):
        kwargs.setdefault("mojeid_registry_endpoint", settings.WEBWHOIS_MOJEID_REGISTRY_ENDPOINT)
        kwargs.setdefault("mojeid_transfer_endpoint", settings.WEBWHOIS_MOJEID_TRANSFER_ENDPOINT)
        kwargs.setdefault("mojeid_link_why", settings.WEBWHOIS_MOJEID_LINK_WHY)
        return super(ContactDetailWithMojeidMixin, self).get_context_data(**kwargs)

    def load_related_objects(self, context):
        super(ContactDetailWithMojeidMixin, self).load_related_objects(context)
        data = context[self._registry_objects_key]["contact"]
        registry_object = data["detail"]
        data["show_button_mojeid"] = bool(self.valid_mojeid_handle_format.match(registry_object.handle)) \
            and not set(registry_object.statuses) & set((
                "mojeidContact",
                "serverTransferProhibited",
                "serverUpdateProhibited",
                "serverDeleteProhibited",
                "deleteCandidate",
                "serverBlocked",
            ))
