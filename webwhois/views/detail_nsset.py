from django.utils.translation import ugettext_lazy as _

from webwhois.utils import WHOIS_MODULE
from webwhois.views.base import RegistryObjectMixin


class NssetDetailMixin(RegistryObjectMixin):

    template_name = "webwhois/nsset.html"

    @classmethod
    def append_nsset_related(cls, data, backend_whois):
        "Load objects related to the nsset and append them into the data context."
        WHOIS = backend_whois
        descriptions = cls._get_status_descriptions("nsset", WHOIS.get_nsset_status_descriptions)
        registry_object = data["detail"]
        data.update({
            "admins": [WHOIS.get_contact_by_handle(handle) for handle in registry_object.tech_contact_handles],
            "registrar": WHOIS.get_registrar_by_handle(registry_object.registrar_handle),
            "status_descriptions": [descriptions[key] for key in registry_object.statuses],
        })

    @classmethod
    def load_registry_object(cls, context, handle, backend):
        "Load nsset of the handle and append it into the context."
        try:
            context[cls._registry_objects_key]["nsset"] = {
                "detail": backend.get_nsset_by_handle(handle),
                "label": _("Nsset"),
                "url_name": context["webwhois"]["detail"]["nsset"]
            }
        except WHOIS_MODULE.OBJECT_NOT_FOUND:
            context["server_exception"] = {
                "title": _("Name server set not found"),
                "message": cls.message_with_handle_in_html(_("No name server set matches %s handle."), handle),
            }
        except WHOIS_MODULE.INVALID_HANDLE:
            context["server_exception"] = cls.message_invalid_handle(handle)

    def load_related_objects(self, context):
        "Load objects related to the nsset and append them into the context."
        self.append_nsset_related(context[self._registry_objects_key]["nsset"], self._WHOIS)
