#
# Copyright (C) 2015-2022  CZ.NIC, z. s. p. o.
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
from django.urls import path, re_path
from django.views.i18n import JavaScriptCatalog

from webwhois.views import (BlockObjectFormView, ContactDetailView, CustomEmailView, DomainDetailView,
                            DownloadEvalFileView, EmailInRegistryView, KeysetDetailView, NotarizedLetterView,
                            NssetDetailView, PersonalInfoFormView, PublicResponseNotFoundView, PublicResponsePdfView,
                            PublicResponseView, RegistrarDetailView, RegistrarListView, ResolveHandleTypeView,
                            ScanResultsView, SendPasswordFormView, ServeNotarizedLetterView, ServeRecordStatementView,
                            UnblockObjectFormView, WhoisFormView)

app_name = 'webwhois'
urlpatterns = [
    path('', WhoisFormView.as_view(), name='form_whois'),
    path('jsi18n/<packages>/', JavaScriptCatalog.as_view(), name='jsi18n'),
    path('object/<handle>/', ResolveHandleTypeView.as_view(), name='registry_object_type'),
    path('contact/<handle>/', ContactDetailView.as_view(), name='detail_contact'),
    path('nsset/<handle>/', NssetDetailView.as_view(), name='detail_nsset'),
    path('keyset/<handle>/', KeysetDetailView.as_view(), name='detail_keyset'),
    path('domain/<handle>/', DomainDetailView.as_view(), name='detail_domain'),
    path('domain/<handle>/scan-results/', ScanResultsView.as_view(), name='scan_results'),
    path('registrar/<handle>/', RegistrarDetailView.as_view(), name='detail_registrar'),
    path('registrars/', RegistrarListView.as_view(), name='registrars'),
    path('registrar-download-evaluation-file/<handle>/', DownloadEvalFileView.as_view(),
         name='download_evaluation_file'),
    path('send-password/', SendPasswordFormView.as_view(), name='form_send_password'),
    path('personal-info/', PersonalInfoFormView.as_view(), name='form_personal_info'),
    path('block-object/', BlockObjectFormView.as_view(), name='form_block_object'),
    path('unblock-object/', UnblockObjectFormView.as_view(), name='form_unblock_object'),
    path('public-response/<public_key>/', PublicResponseView.as_view(), name='public_response'),
    path('public-response/<public_key>/pdf/', PublicResponsePdfView.as_view(), name='public_response_pdf'),
    path('response-not-found/<public_key>/', PublicResponseNotFoundView.as_view(), name='response_not_found'),
    path('email-in-registry/<public_key>/', EmailInRegistryView.as_view(), name='email_in_registry_response'),
    path('custom-email/<public_key>/', CustomEmailView.as_view(), name='custom_email_response'),
    path('notarized-letter/<public_key>/', NotarizedLetterView.as_view(), name='notarized_letter_response'),
    path('pdf-notarized-letter/<public_key>/', ServeNotarizedLetterView.as_view(), name='notarized_letter_serve_pdf'),
    re_path(r'^verified-record-statement-pdf/(?P<object_type>(contact|domain|nsset|keyset))/(?P<handle>[^/]+)/$',
            ServeRecordStatementView.as_view(), name='record_statement_pdf'),
]
