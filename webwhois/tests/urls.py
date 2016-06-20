from django.conf.urls import include, patterns, url

urlpatterns = patterns(
    '',
    url(r'^whois/', include('webwhois.urls', namespace='webwhois')),
)
