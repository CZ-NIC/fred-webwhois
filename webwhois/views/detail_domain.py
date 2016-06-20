import re

import idna
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import pgettext_lazy, ugettext_lazy as _

from webwhois.views import KeysetDetailMixin, NssetDetailMixin
from webwhois.views.base import RegistryObjectMixin


class DomainDetailMixin(RegistryObjectMixin):

    template_name = "webwhois/domain.html"

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
    def load_registry_object(cls, context, handle, backend, handle_is_domain=True):
        """
        Load domain of the handle and append it into the context.

        Param 'handle_is_domain' has an impact on error message.
        """
        CORBA, WHOIS = backend

        if handle.startswith("."):
            context["server_exception"] = cls.message_invalid_handle(handle)
            return

        try:
            idna_handle = idna.encode(handle)
        except idna.IDNAError:
            if handle_is_domain:
                context["server_exception"] = cls.message_invalid_handle(handle)
            else:
                context["server_exception"] = {
                    "title": _("Handle not found"),
                    "message": cls.message_with_handle_in_html(
                        _("No domain, contact or name server set matches %s query."), handle)
                }
            return

        try:
            context[cls._registry_objects_key]["domain"] = {
                "detail": WHOIS.get_domain_by_handle(idna_handle),
                "label": pgettext_lazy("singular", "Domain"),
                "url_name": context["webwhois"]["detail"]["domain"],
            }
        except CORBA.Registry.Whois.OBJECT_NOT_FOUND:
            # Only handle with format of valid domain name and in managed zone raises OBJECT_NOT_FOUND.
            context["server_exception"] = cls.make_message_not_found(handle, handle_is_domain)
            context["server_exception"]["handle_is_in_zone"] = True
            context["HOW_TO_REGISTER_LINK"] = check_context(settings.WEBWHOIS_HOW_TO_REGISTER_LINK)
        except CORBA.Registry.Whois.UNMANAGED_ZONE:
            # Handle in domain invalid format raises UNMANAGED_ZONE instead of OBJECT_NOT_FOUND.
            if "." in handle:
                context["managed_zone_list"] = WHOIS.get_managed_zone_list()
                context["WHOIS_SEARCH_ENGINES"] = check_links(settings.WEBWHOIS_SEARCH_ENGINES)
                context["server_exception"] = {
                    "title": _("Unmanaged zone"),
                    "message": cls.message_with_handle_in_html(
                        _("Domain %s cannot be found in the registry. "
                          "You can search for domains in the these zones only:"), handle),
                    "unmanaged_zone": True,
                }
            else:
                context["server_exception"] = cls.make_message_not_found(handle, handle_is_domain)
        except CORBA.Registry.Whois.INVALID_LABEL:
            # Pattern for the handle is more vague than the pattern of domain name format.
            context["server_exception"] = cls.message_invalid_handle(handle)
        except CORBA.Registry.Whois.TOO_MANY_LABELS:
            # Caution! Domain name can have more than one fullstop character and it is still valid.
            # for example: '0.2.4.e164.arpa'
            # remove subdomain names: 'www.sub.domain.cz' -> 'domain.cz'
            context["example_domain_name"] = re.search("([^.]+\.\w+)$", handle, re.IGNORECASE).group(1)
            context["server_exception"] = {
                "title": _("Incorrect input"),
                "too_many_parts_in_domain_name": True,
            }

    def load_related_objects(self, context):
        "Load objects related to the domain and append them into the context."
        descriptions = self._get_status_descriptions("domain", self._WHOIS.get_domain_status_descriptions)
        data = context[self._registry_objects_key]["domain"]  # detail, type, label, href
        registry_object = data["detail"]
        data.update({
            "registrant": self._WHOIS.get_contact_by_handle(registry_object.registrant_handle),
            "registrar": self._WHOIS.get_registrar_by_handle(registry_object.registrar_handle),
            "admins": [self._WHOIS.get_contact_by_handle(handle) for handle in registry_object.admin_contact_handles],
            "status_descriptions": [descriptions[key] for key in registry_object.statuses],
        })
        if registry_object.nsset_handle:
            data["nsset"] = {"detail": self._WHOIS.get_nsset_by_handle(registry_object.nsset_handle)}
            NssetDetailMixin.append_nsset_related(data["nsset"], self._WHOIS)
        if registry_object.keyset_handle:
            data["keyset"] = {"detail": self._WHOIS.get_keyset_by_handle(registry_object.keyset_handle)}
            KeysetDetailMixin.append_keyset_related(data["keyset"], self._WHOIS)

    def get_context_data(self, **kwargs):
        kwargs.setdefault("DNSSEC_URL", settings.WEBWHOIS_DNSSEC_URL)
        return super(DomainDetailMixin, self).get_context_data(**kwargs)


def check_context(link):
    "Check if link context has keys required by the template."
    if link and not (link.get("href") and link.get("label")):
        raise ImproperlyConfigured("Data %s does not have requred keys." % link)
    return link


def check_links(links):
    "Check if list of link contexts has keys required by the template."
    for link in links:
        check_context(link)
    return links
