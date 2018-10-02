from __future__ import unicode_literals

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from webwhois.utils import WHOIS
from webwhois.views import ContactDetailMixin, DomainDetailMixin, KeysetDetailMixin, NssetDetailMixin
from webwhois.views.base import RegistryObjectMixin
from webwhois.views.registrar import RegistrarDetailMixin


class ResolveHandleTypeMixin(RegistryObjectMixin):
    """Find all objects with the handle."""

    multiple_entries_template = "webwhois/multiple_entries.html"
    object_type_name = "multiple"

    @classmethod
    def load_registry_object(cls, context, handle):
        """Load all registry objects of the handle and append it into the context."""
        ContactDetailMixin.load_registry_object(context, handle)
        NssetDetailMixin.load_registry_object(context, handle)
        KeysetDetailMixin.load_registry_object(context, handle)
        RegistrarDetailMixin.load_registry_object(context, handle)
        DomainDetailMixin.load_registry_object(context, handle)

        if not context[cls._registry_objects_key]:
            # No object was found. Create a virtual server exception to render its template.
            # TODO: This solution is hopefully temporary and should be removed very soon.
            context["server_exception"] = {
                "code": "OBJECT_NOT_FOUND",
                "title": _("Record not found"),
                "message": cls.message_with_handle_in_html(_("%s does not match any record."), handle),
                "object_not_found": True,
            }
            context["managed_zone_list"] = WHOIS.get_managed_zone_list()

    def load_related_objects(self, context):
        """Prepare url for redirect to the registry object type."""
        registry_object_type = list(context[self._registry_objects_key].keys())[0]
        url = reverse("webwhois:detail_%s" % registry_object_type, kwargs={"handle": self.kwargs["handle"]},
                      current_app=self.request.resolver_match.namespace)
        context.setdefault("redirect_to_type", url)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if "redirect_to_type" in context:
            return HttpResponseRedirect(context["redirect_to_type"])
        return super(ResolveHandleTypeMixin, self).get(request, *args, **kwargs)

    def get_template_names(self):
        context = self._get_registry_objects()
        if len(context[self._registry_objects_key]) > 1:
            return [self.multiple_entries_template]
        return super(ResolveHandleTypeMixin, self).get_template_names()


class ResolveHandleTypeView(ResolveHandleTypeMixin, TemplateView):
    """View which searches all types of objects."""
