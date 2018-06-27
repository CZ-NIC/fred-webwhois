from __future__ import unicode_literals

from django.conf.urls import include, url

from webwhois.views import ServeRecordStatementView, WhoisFormView

urlpatterns = [
    url(r'^whois/', include('webwhois.urls', namespace='webwhois')),
    # urls required by 404:
    url(r'^$', WhoisFormView.as_view(), name='home_page'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^test-record-statement-pdf/(?P<object_type>(\w+))/(?P<handle>.{1,255})/$',
        ServeRecordStatementView.as_view(), name='test_record_statement_pdf'),
]
