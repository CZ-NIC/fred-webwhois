import re

from django.conf.urls import include, url
from django.views.i18n import javascript_catalog
from webwhois_standalone.views import DobradomenaServeFile, HomePageView

from webwhois.settings import WEBWHOIS_DOBRADOMENA_FILE_NAME, WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN

urlpatterns = [
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/(?P<packages>\S+?)/$', javascript_catalog, name='jsi18n'),
    url(r'^$', HomePageView.as_view(), name='home_page'),
    url(r'^whois/', include('webwhois_standalone.urls', namespace='standalone_webwhois', app_name='webwhois')),
    url(r'^basic-whois/', include('webwhois.urls', namespace='basic_webwhois', app_name='webwhois')),
]

# Serve files if they are a part of the site.
if WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN and not re.match("https?://", WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN):
    dobradomena_path = re.sub("%\((\w+)\)s", "(?P<\\1>.+)",
                              WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN) + WEBWHOIS_DOBRADOMENA_FILE_NAME
    dobradomena_path = '^' + dobradomena_path.lstrip("/") + '$'
    urlpatterns += [
        url(dobradomena_path, DobradomenaServeFile.as_view(), name='dobradomena_download_manual'),
    ]
