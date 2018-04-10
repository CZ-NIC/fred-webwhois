from __future__ import unicode_literals

from django.conf.urls import url

from webwhois.views.pages import WebwhoisBlockObjectFormView, WebwhoisContactDetailView, WebwhoisCustomEmailView, \
    WebwhoisDomainDetailView, WebwhoisDownloadEvalFileView, WebwhoisEmailInRegistryView, WebwhoisFormView, \
    WebwhoisKeysetDetailView, WebwhoisNotarizedLetterView, WebwhoisNssetDetailView, WebwhoisPersonalInfoFormView, \
    WebwhoisPublicResponseNotFoundView, WebwhoisRegistrarDetailView, WebwhoisRegistrarListView, \
    WebwhoisResolveHandleTypeView, WebwhoisSendPasswordFormView, WebwhoisServeNotarizedLetterView, \
    WebwhoisServeRecordStatementView, WebwhoisUnblockObjectFormView

app_name = 'webwhois'
urlpatterns = [
    url(r'^$', WebwhoisFormView.as_view(), name='form_whois'),
    url(r'^object/(?P<handle>.{1,255})/$', WebwhoisResolveHandleTypeView.as_view(), name='registry_object_type'),
    url(r'^contact/(?P<handle>.{1,255})/$', WebwhoisContactDetailView.as_view(), name='detail_contact'),
    url(r'^nsset/(?P<handle>.{1,255})/$', WebwhoisNssetDetailView.as_view(), name='detail_nsset'),
    url(r'^keyset/(?P<handle>.{1,255})/$', WebwhoisKeysetDetailView.as_view(), name='detail_keyset'),
    url(r'^domain/(?P<handle>.{1,255})/$', WebwhoisDomainDetailView.as_view(), name='detail_domain'),
    url(r'^registrar/(?P<handle>.{1,255})/$', WebwhoisRegistrarDetailView.as_view(), name='detail_registrar'),
    url(r'^registrars/$', WebwhoisRegistrarListView.as_view(is_retail=True), name='registrar_list_retail'),
    url(r'^registrars/wholesale/$', WebwhoisRegistrarListView.as_view(), name='registrar_list_wholesale'),
    url(r'^registrar-download-evaluation-file/(?P<handle>.{1,255})/$', WebwhoisDownloadEvalFileView.as_view(),
        name='download_evaluation_file'),
    url(r'^send-password/$', WebwhoisSendPasswordFormView.as_view(), name='form_send_password'),
    url(r'^personal-info/$', WebwhoisPersonalInfoFormView.as_view(), name='form_personal_info'),
    url(r'^block-object/$', WebwhoisBlockObjectFormView.as_view(), name='form_block_object'),
    url(r'^unblock-object/$', WebwhoisUnblockObjectFormView.as_view(), name='form_unblock_object'),
    url(r'^response-not-found/(?P<public_key>\w{64})/$', WebwhoisPublicResponseNotFoundView.as_view(),
        name='response_not_found'),
    url(r'^email-in-registry/(?P<public_key>\w{64})/$', WebwhoisEmailInRegistryView.as_view(),
        name='email_in_registry_response'),
    url(r'^custom-email/(?P<public_key>\w{64})/$', WebwhoisCustomEmailView.as_view(),
        name='custom_email_response'),
    url(r'^notarized-letter/(?P<public_key>\w{64})/$', WebwhoisNotarizedLetterView.as_view(),
        name='notarized_letter_response'),
    url(r'^pdf-notarized-letter/(?P<public_key>\w{64})/$', WebwhoisServeNotarizedLetterView.as_view(),
        name='notarized_letter_serve_pdf'),
    url(r'^verified-record-statement-pdf/(?P<object_type>(contact|domain|nsset|keyset))/(?P<handle>.{1,255})/$',
        WebwhoisServeRecordStatementView.as_view(), name='record_statement_pdf'),
]
