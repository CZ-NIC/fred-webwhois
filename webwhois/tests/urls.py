from django.conf.urls import include, url

from webwhois.views.pages import WebwhoisFormView, WebwhoisServeRecordStatementView

urlpatterns = [
    url(r'^whois/', include('webwhois.urls', namespace='webwhois')),
    # urls required by 404:
    url(r'^$', WebwhoisFormView.as_view(), name='home_page'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^test-record-statement-pdf/(?P<object_type>(\w+))/(?P<handle>.{1,255})/$',
        WebwhoisServeRecordStatementView.as_view(), name='test_record_statement_pdf'),
]
