"""URLs definition for webwhois site."""
from django.urls import include, path

urlpatterns = [
    path('', include('webwhois.urls')),
]
