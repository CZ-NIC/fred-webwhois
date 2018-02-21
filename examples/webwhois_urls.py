"""URLs definition for webwhois site."""
from django.conf.urls import include, url

urlpatterns = [
    url(r'^', include('webwhois.urls')),
]
