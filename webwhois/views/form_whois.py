#
# Copyright (C) 2015-2020  CZ.NIC, z. s. p. o.
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
