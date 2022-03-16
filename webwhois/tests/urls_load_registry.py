#
# Copyright (C) 2021  CZ.NIC, z. s. p. o.
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

from webwhois.views import RegistrarListView, ScanResultsView, WhoisFormView

from .views import (LoadContactDetailView, LoadDomainDetailView, LoadKeysetDetailView, LoadNssetDetailView,
                    LoadRegistrarDetailView, LoadResolveHandleTypeView)

urls = [
    path('object/<handle>/', LoadResolveHandleTypeView.as_view(), name='registry_object_type'),
    path('contact/<handle>/', LoadContactDetailView.as_view(), name='detail_contact'),
    path('nsset/<handle>/', LoadNssetDetailView.as_view(), name='detail_nsset'),
    path('keyset/<handle>/', LoadKeysetDetailView.as_view(), name='detail_keyset'),
    path('domain/<handle>/', LoadDomainDetailView.as_view(), name='detail_domain'),
    path('registrar/<handle>/', LoadRegistrarDetailView.as_view(), name='detail_registrar'),
    # Paths for reverses.
    path('', WhoisFormView.as_view(), name='form_whois'),
    path('domain/<handle>/scan-results/', ScanResultsView.as_view(), name='scan_results'),
    path('registrars/', RegistrarListView.as_view(), name='registrars'),
]

urlpatterns = [
    path('', include((urls, 'webwhois'))),
]
