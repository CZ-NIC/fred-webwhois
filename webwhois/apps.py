"""AppConfig definition."""
from __future__ import unicode_literals

from django.apps import AppConfig

from .settings import WebwhoisAppSettings


class WebwhoisAppConfig(AppConfig):
    name = 'webwhois'

    def ready(self):
        WebwhoisAppSettings.check()
