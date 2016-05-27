import re

from django.conf import settings
from django.conf.urls import include, patterns, url
from webwhois_standalone.views import DobradomenaServeFile, HomePageView

urlpatterns = patterns('',
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^$', HomePageView.as_view(), name='home_page'),
    url(r'^whois/', include('webwhois_standalone.urls', namespace='standalone_webwhois', app_name='webwhois')),
    url(r'^basic-whois/', include('webwhois.urls', namespace='basic_webwhois', app_name='webwhois')),
)

# Serve files if they are a part of the site.
if not re.match("https?://", settings.WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN):
    dobradomena_path = re.sub("%\((\w+)\)s", "(?P<\\1>.+)", settings.WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN) + settings.WEBWHOIS_DOBRADOMENA_FILE_NAME
    dobradomena_path = '^' + dobradomena_path.lstrip("/") + '$'
    urlpatterns += patterns('',
        url(dobradomena_path, DobradomenaServeFile.as_view(), name='dobradomena_download_manual'),
    )
