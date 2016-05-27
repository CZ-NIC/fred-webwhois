from django.conf.urls import patterns, url

from .views import PublicRequestView, WebwhoisContactDetailView, WebwhoisDomainDetailView, \
    WebwhoisDownloadEvalFileView, WebwhoisFormView, WebwhoisKeysetDetailView, WebwhoisNssetDetailView, \
    WebwhoisRegistrarDetailView, WebwhoisRegistrarListView, WebwhoisResolveHandleTypeView

# WebWhois_standalone site urls.
urlpatterns = patterns('',
    url(r'^form/$', WebwhoisFormView.as_view(), name='form_whois'),
    url(r'^object/(?P<handle>[\w_.:-]{1,255})/$', WebwhoisResolveHandleTypeView.as_view(), name='registry_object_type'),
    url(r'^contact/(?P<handle>[\w_.:-]{1,255})/$', WebwhoisContactDetailView.as_view(), name='detail_contact'),
    url(r'^nsset/(?P<handle>[\w_.:-]{1,255})/$', WebwhoisNssetDetailView.as_view(), name='detail_nsset'),
    url(r'^keyset/(?P<handle>[\w_.:-]{1,255})/$', WebwhoisKeysetDetailView.as_view(), name='detail_keyset'),
    url(r'^domain/(?P<handle>[\w_.:-]{1,255})/$', WebwhoisDomainDetailView.as_view(), name='detail_domain'),
    url(r'^registrar/(?P<handle>[\w_.:-]{1,255})/$', WebwhoisRegistrarDetailView.as_view(), name='detail_registrar'),
    url(r'^registrars/$', WebwhoisRegistrarListView.as_view(is_retail=True), name='registrar_list_retail'),
    url(r'^registrars/wholesale/$', WebwhoisRegistrarListView.as_view(), name='registrar_list_wholesale'),
    url(r'^public-request/$', PublicRequestView.as_view(), name='form_public_request'),
    url(r'^registrar-download-evaluation-file/(?P<handle>[\w_.:-]{1,255})/$', WebwhoisDownloadEvalFileView.as_view(),
        name='download_evaluation_file'),
)
