#
# Copyright (C) 2015-2021  CZ.NIC, z. s. p. o.
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
#
from django.urls import include, path

from webwhois.views import RegistrarListView, ServeRecordStatementView, WhoisFormView
from webwhois.views.public_request import BaseResponseTemplateView

from .views import CustomRegistrarListView, GetObjectRegistryView, LoadObjectRegistryView

urlpatterns = [
    path('whois/', include('webwhois.urls', namespace='webwhois')),
    # urls required by 404:
    path('', WhoisFormView.as_view(), name='home_page'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('registry_mixin/get_object/', GetObjectRegistryView.as_view(), kwargs={'handle': 'kryten'}),
    path('registry_mixin/load_registry/', LoadObjectRegistryView.as_view(), kwargs={'handle': 'kryten'}),
    path('test-record-statement-pdf/<object_type>/<handle>/', ServeRecordStatementView.as_view(),
         name='test_record_statement_pdf'),
    path('base-public-response/', BaseResponseTemplateView.as_view(template_name='public_response.html'),
         kwargs={'public_key': 'test-public-key'}),
    # URLs for TestRegistrarListView
    path('registrars/red-dwarf/', RegistrarListView.as_view(group_name='red_dwarf'), name='registrars_red_dwarf'),
    path('registrars/custom/', CustomRegistrarListView.as_view(), name='registrars_custom'),
]
