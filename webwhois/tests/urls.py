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
from django.conf.urls import include, url

from webwhois.views import RegistrarListView, ServeRecordStatementView, WhoisFormView
from webwhois.views.public_request import BaseResponseTemplateView

from .views import CustomRegistrarListView

urlpatterns = [
    url(r'^whois/', include('webwhois.urls', namespace='webwhois')),
    # urls required by 404:
    url(r'^$', WhoisFormView.as_view(), name='home_page'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^test-record-statement-pdf/(?P<object_type>(\w+))/(?P<handle>.{1,255})/$',
        ServeRecordStatementView.as_view(), name='test_record_statement_pdf'),
    url(r'^base-public-response/$',
        BaseResponseTemplateView.as_view(template_name='public_response.html'),
        kwargs={'public_key': 'test-public-key'}),
    # URLs for TestRegistrarListView
    url(r'^registrars/red-dwarf/$', RegistrarListView.as_view(group_name='red_dwarf'), name='registrars_red_dwarf'),
    url(r'^registrars/retail/$', RegistrarListView.as_view(is_retail=True), name='registrars_retail'),
    url(r'^registrars/wholesale/$', RegistrarListView.as_view(is_retail=False), name='registrars_wholesale'),
    url(r'^registrars/custom/$', CustomRegistrarListView.as_view(), name='registrars_custom'),
]
