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
from django.conf.urls import url
from django.views.i18n import JavaScriptCatalog

from webwhois.views import BlockObjectFormView, ContactDetailView, CustomEmailView, DomainDetailView, \
    DownloadEvalFileView, EmailInRegistryView, KeysetDetailView, NotarizedLetterView, NssetDetailView, \
    PersonalInfoFormView, PublicResponseNotFoundView, RegistrarDetailView, RegistrarListView, ResolveHandleTypeView, \
    SendPasswordFormView, ServeNotarizedLetterView, ServeRecordStatementView, UnblockObjectFormView, WhoisFormView

app_name = 'webwhois'
urlpatterns = [
    url(r'^$', WhoisFormView.as_view(), name='form_whois'),
    url(r'^jsi18n/(?P<packages>\S+?)/$', JavaScriptCatalog.as_view(), name='jsi18n'),
    url(r'^object/(?P<handle>.{1,255})/$', ResolveHandleTypeView.as_view(), name='registry_object_type'),
    url(r'^contact/(?P<handle>.{1,255})/$', ContactDetailView.as_view(), name='detail_contact'),
    url(r'^nsset/(?P<handle>.{1,255})/$', NssetDetailView.as_view(), name='detail_nsset'),
    url(r'^keyset/(?P<handle>.{1,255})/$', KeysetDetailView.as_view(), name='detail_keyset'),
    url(r'^domain/(?P<handle>.{1,255})/$', DomainDetailView.as_view(), name='detail_domain'),
    url(r'^registrar/(?P<handle>.{1,255})/$', RegistrarDetailView.as_view(), name='detail_registrar'),
    url(r'^registrars/$', RegistrarListView.as_view(), name='registrars'),
    url(r'^registrar-download-evaluation-file/(?P<handle>.{1,255})/$', DownloadEvalFileView.as_view(),
        name='download_evaluation_file'),
    url(r'^send-password/$', SendPasswordFormView.as_view(), name='form_send_password'),
    url(r'^personal-info/$', PersonalInfoFormView.as_view(), name='form_personal_info'),
    url(r'^block-object/$', BlockObjectFormView.as_view(), name='form_block_object'),
    url(r'^unblock-object/$', UnblockObjectFormView.as_view(), name='form_unblock_object'),
    url(r'^response-not-found/(?P<public_key>\w{64})/$', PublicResponseNotFoundView.as_view(),
        name='response_not_found'),
    url(r'^email-in-registry/(?P<public_key>\w{64})/$', EmailInRegistryView.as_view(),
        name='email_in_registry_response'),
    url(r'^custom-email/(?P<public_key>\w{64})/$', CustomEmailView.as_view(), name='custom_email_response'),
    url(r'^notarized-letter/(?P<public_key>\w{64})/$', NotarizedLetterView.as_view(), name='notarized_letter_response'),
    url(r'^pdf-notarized-letter/(?P<public_key>\w{64})/$', ServeNotarizedLetterView.as_view(),
        name='notarized_letter_serve_pdf'),
    url(r'^verified-record-statement-pdf/(?P<object_type>(contact|domain|nsset|keyset))/(?P<handle>.{1,255})/$',
        ServeRecordStatementView.as_view(), name='record_statement_pdf'),
]
