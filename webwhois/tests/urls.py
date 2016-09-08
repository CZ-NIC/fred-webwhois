from django.conf.urls import include, patterns, url

from webwhois.views.pages import WebwhoisFormView

urlpatterns = patterns(
    '',
    url(r'^whois/', include('webwhois.urls', namespace='webwhois')),
    # urls required by 404:
    url(r'^$', WebwhoisFormView.as_view(), name='home_page'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
)
