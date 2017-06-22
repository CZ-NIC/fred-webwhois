from django.urls import reverse
from django.views.generic import FormView

from webwhois.forms import WhoisForm
from webwhois.views.base import BaseContextMixin


class WhoisFormView(BaseContextMixin, FormView):

    template_name = 'webwhois/form_whois.html'
    form_class = WhoisForm

    def get_initial(self):
        data = self.initial.copy()
        data["handle"] = self.request.GET.get("handle")
        return data

    def form_valid(self, form):
        self.success_url = reverse("webwhois:registry_object_type", kwargs={"handle": form.cleaned_data['handle']},
                                   current_app=self.request.resolver_match.namespace)
        return super(WhoisFormView, self).form_valid(form)
