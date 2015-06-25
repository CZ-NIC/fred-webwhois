from django.conf.urls import patterns, include, url

from .views import DomainDetailView, ContactDetailView, NssetDetailView, KeysetDetailView,\
    RegistrarDetailView, WhoisQueryView, RegistrarsListView, DownloadEvalFileView

urlpatterns = patterns('',
    url(r'^$', WhoisQueryView.as_view(), name='query'),
    url(r'^captcha/(?P<handle>.{1,255})$', WhoisQueryView.as_view(), name='captcha'),
    url(r'^domain/(?P<handle>[a-zA-Z0-9_\.\-]{1,255})$', DomainDetailView.as_view(), name='domain'),
    url(r'^contact/(?P<handle>[A-Z0-9_\:\.\-]{1,255})$', ContactDetailView.as_view(), name='contact'),
    url(r'^nsset/(?P<handle>[A-Z0-9_\:\.\-]{1,255})$', NssetDetailView.as_view(), name='nsset'),
    url(r'^keyset/(?P<handle>[A-Z0-9_\:\.\-]{1,255})$', KeysetDetailView.as_view(), name='keyset'),
    url(r'^registrar/(?P<handle>[A-Z0-9_\:\.\-]{1,255})$', RegistrarDetailView.as_view(), name='registrar'),
    url(r'^registrars/$', RegistrarsListView.as_view(), {"retail": True}, name='registrars'),
    url(r'^registrars/wholesale$', RegistrarsListView.as_view(), {"retail": False}, name='registrars_wholesale'),
    url(r'^registrar/(?P<handle>[A-Z0-9_\:\.\-]{1,255})/download_eval$', DownloadEvalFileView.as_view(),
        name='download_eval_file'),
)
