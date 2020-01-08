#
# Copyright (C) 2017-2020  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

"""Tests of`webwhois.settings` module."""
from unittest.mock import patch, sentinel

from django.conf import settings
from django.test import SimpleTestCase

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
