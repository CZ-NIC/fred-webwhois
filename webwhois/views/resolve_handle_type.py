from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from webwhois.views import ContactDetailMixin, DomainDetailMixin, KeysetDetailMixin, NssetDetailMixin
from webwhois.views.base import RegistryObjectMixin
from webwhois.views.registrar import RegistrarDetailMixin


class ResolveHandleTypeMixin(RegistryObjectMixin):
    "Find all objects with the handle."

    multiple_entries_template = "webwhois/multiple_entries.html"
    object_type_name = "multiple"

    @classmethod
    def load_registry_object(cls, context, handle, backend):
        "Load all registry objects of the handle and append it into the context."
        ContactDetailMixin.load_registry_object(context, handle, backend)
        NssetDetailMixin.load_registry_object(context, handle, backend)
        KeysetDetailMixin.load_registry_object(context, handle, backend)
        RegistrarDetailMixin.load_registry_object(context, handle, backend)
        # handle_is_domain = False - It is not known whether that handle is a domain.
        # It has an impact on error message.
        DomainDetailMixin.load_registry_object(context, handle, backend, handle_is_domain=False)

    def load_related_objects(self, context):
        "Prepare url for redirect to the registry object type."
        registry_object_type = context[self._registry_objects_key].keys()[0]
        url = reverse("webwhois:detail_%s" % registry_object_type, kwargs={"handle":  self.kwargs["handle"]},
                      current_app=self.request.resolver_match.namespace)
        context.setdefault("redirect_to_type", url)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if "redirect_to_type" in context:
            return HttpResponseRedirect(context["redirect_to_type"])
        return super(ResolveHandleTypeMixin, self).get(request, *args, **kwargs)

    def get_context_data(self, handle, **kwargs):
        context = super(ResolveHandleTypeMixin, self).get_context_data(handle, **kwargs)
        if context["number_of_found_objects"] > 1:
            self.template_name = self.multiple_entries_template
        return context
