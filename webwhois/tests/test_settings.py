"""Tests of`webwhois.settings` module."""
from __future__ import unicode_literals

from django.conf import settings
from django.test import SimpleTestCase
from mock import patch, sentinel

from webwhois.settings import WEBWHOIS_SETTINGS


class TestSettings(SimpleTestCase):
    """Test `WebwhoisAppSettings` class."""

    def test_logger_corba_ior_default(self):
        with self.settings():
            del settings.WEBWHOIS_CORBA_NETLOC
            del settings.WEBWHOIS_LOGGER_CORBA_NETLOC
            # Empty settings override doesn't clear cache
            WEBWHOIS_SETTINGS.invalidate_cache()

            self.assertEqual(WEBWHOIS_SETTINGS.LOGGER_CORBA_NETLOC, 'localhost')

    def test_logger_corba_ior_environ(self):
        with patch.dict('os.environ', {'FRED_WEBWHOIS_NETLOC': 'environment_ior'}):
            with self.settings():
                del settings.WEBWHOIS_CORBA_NETLOC
                del settings.WEBWHOIS_LOGGER_CORBA_NETLOC
                # Empty settings override doesn't clear cache
                WEBWHOIS_SETTINGS.invalidate_cache()

                self.assertEqual(WEBWHOIS_SETTINGS.LOGGER_CORBA_NETLOC, 'environment_ior')

    def test_logger_corba_ior_copy(self):
        # Ensure WEBWHOIS_CORBA_NETLOC is used if defined
        with self.settings(WEBWHOIS_CORBA_NETLOC=sentinel.ior):
            del settings.WEBWHOIS_LOGGER_CORBA_NETLOC

            self.assertEqual(WEBWHOIS_SETTINGS.LOGGER_CORBA_NETLOC, sentinel.ior)

    def test_logger_corba_context_default(self):
        with self.settings():
            del settings.WEBWHOIS_CORBA_CONTEXT
            del settings.WEBWHOIS_LOGGER_CORBA_CONTEXT
            # Empty settings override doesn't clear cache
            WEBWHOIS_SETTINGS.invalidate_cache()

            self.assertEqual(WEBWHOIS_SETTINGS.LOGGER_CORBA_CONTEXT, 'fred')

    def test_logger_corba_context_copy(self):
        # Ensure WEBWHOIS_CORBA_CONTEXT is used if defined
        with self.settings(WEBWHOIS_CORBA_CONTEXT=sentinel.context):
            del settings.WEBWHOIS_LOGGER_CORBA_CONTEXT

            self.assertEqual(WEBWHOIS_SETTINGS.LOGGER_CORBA_CONTEXT, sentinel.context)
