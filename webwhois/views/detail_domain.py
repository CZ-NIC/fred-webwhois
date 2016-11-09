import re

import idna
from django.utils.translation import pgettext_lazy, ugettext_lazy as _

from webwhois.settings import WEBWHOIS_DNSSEC_URL, WEBWHOIS_HOW_TO_REGISTER_LINK, WEBWHOIS_SEARCH_ENGINES
from webwhois.utils import WHOIS, WHOIS_MODULE
from webwhois.views import KeysetDetailMixin, NssetDetailMixin
from webwhois.views.base import RegistryObjectMixin


class DomainDetailMixin(RegistryObjectMixin):

    template_name = "webwhois/domain.html"
    object_type_name = "domain"

    @classmethod
    def make_message_not_found(cls, handle, handle_is_domain):
        "Handle or domain not found."
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
            idna_handle = idna.encode(handle)
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
                "label": pgettext_lazy("singular", "Domain"),
            }
        except WHOIS_MODULE.OBJECT_NOT_FOUND:
            # Only handle with format of valid domain name and in managed zone raises OBJECT_NOT_FOUND.
            context["server_exception"] = cls.make_message_not_found(handle, handle_is_domain)
            context["server_exception"]["handle_is_in_zone"] = True
            context["HOW_TO_REGISTER_LINK"] = WEBWHOIS_HOW_TO_REGISTER_LINK
        except WHOIS_MODULE.UNMANAGED_ZONE:
            # Handle in domain invalid format raises UNMANAGED_ZONE instead of OBJECT_NOT_FOUND.
            if "." in handle:
                context["managed_zone_list"] = WHOIS.get_managed_zone_list()
                context["WHOIS_SEARCH_ENGINES"] = WEBWHOIS_SEARCH_ENGINES
                context["server_exception"] = {
                    "code": "UNMANAGED_ZONE",
                    "title": _("Unmanaged zone"),
                    "message": cls.message_with_handle_in_html(
                        _("Domain %s cannot be found in the registry. "
                          "You can search for domains in the these zones only:"), handle),
                    "unmanaged_zone": True,
                }
            else:
                context["server_exception"] = cls.make_message_not_found(handle, handle_is_domain)
        except WHOIS_MODULE.INVALID_LABEL:
            # Pattern for the handle is more vague than the pattern of domain name format.
            context["server_exception"] = cls.message_invalid_handle(handle, "INVALID_LABEL")
        except WHOIS_MODULE.TOO_MANY_LABELS:
            # Caution! Domain name can have more than one fullstop character and it is still valid.
            # for example: '0.2.4.e164.arpa'
            # remove subdomain names: 'www.sub.domain.cz' -> 'domain.cz'
            context["example_domain_name"] = re.search("([^.]+\.\w+)\.?$", handle, re.IGNORECASE).group(1)
            context["server_exception"] = {
                "code": "TOO_MANY_LABELS",
                "title": _("Incorrect input"),
                "too_many_parts_in_domain_name": True,
            }

    def load_related_objects(self, context):
        "Load objects related to the domain and append them into the context."
        descriptions = self._get_status_descriptions("domain", WHOIS.get_domain_status_descriptions)
        data = context[self._registry_objects_key]["domain"]  # detail, type, label, href
        registry_object = data["detail"]
        data["status_descriptions"] = [descriptions[key] for key in registry_object.statuses]
        data["show_details"] = True
        if "deleteCandidate" in registry_object.statuses:
            data["show_details"] = False
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
