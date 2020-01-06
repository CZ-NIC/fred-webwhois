#
# Copyright (C) 2018-2020  CZ.NIC, z. s. p. o.
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

"""Test `webwhois.utils.public_response` module."""
import warnings
from datetime import date
from unittest.mock import patch, sentinel

from django.test import SimpleTestCase
from testfixtures import Replace, ShouldWarn, test_date

from webwhois.utils.public_response import BlockResponse, PersonalInfoResponse, PublicResponse, SendPasswordResponse


class TestPublicResponse(SimpleTestCase):
    """Test `PublicResponse` class."""

    def test_init_no_confirmation_method(self):
        with ShouldWarn(DeprecationWarning("Argument confirmation_method will be required.")):
            warnings.simplefilter('always')
            public_response = PublicResponse(sentinel.object_type, sentinel.public_request_id, sentinel.request_type,
                                             sentinel.handle)
        self.assertIsNone(public_response.confirmation_method)

    def test_create_date_naive(self):
        with self.settings(USE_TZ=False):
            with Replace('webwhois.utils.public_response.date', test_date(2017, 5, 25)):
                public_response = PublicResponse(sentinel.object_type, sentinel.public_request_id,
                                                 sentinel.request_type, sentinel.handle, sentinel.confirmation_method)
        self.assertEqual(public_response.create_date, date(2017, 5, 25))

    def test_create_date_aware(self):
        with self.settings(USE_TZ=True):
            with patch('webwhois.utils.public_response.localdate', return_value=date(2017, 5, 25)):
                public_response = PublicResponse(sentinel.object_type, sentinel.public_request_id,
                                                 sentinel.request_type, sentinel.handle, sentinel.confirmation_method)
        self.assertEqual(public_response.create_date, date(2017, 5, 25))

    def test_repr(self):
        public_response = PublicResponse('smeg_head', 16, sentinel.request_type, 'rimmer', sentinel.confirmation_method)
        self.assertEqual(repr(public_response), '<PublicResponse smeg_head rimmer 16>')

    def test_repr_unicode(self):
        public_response = PublicResponse('ěščř', 16, sentinel.request_type, 'rimmer', sentinel.confirmation_method)
        string = '<PublicResponse ěščř rimmer 16>'
        self.assertEqual(repr(public_response), string)

    def test_equality(self):
        pr_rimmer = PublicResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.confirmation_method)
        pr_clone = PublicResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.confirmation_method)
        pr_kryten = PublicResponse('android', 'K', sentinel.request_type, 'kryten', sentinel.confirmation_method)

        self.assertTrue(pr_rimmer == pr_rimmer)
        self.assertTrue(pr_rimmer == pr_clone)
        self.assertFalse(pr_rimmer == pr_kryten)

    def test_inequality(self):
        pr_rimmer = PublicResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.confirmation_method)
        pr_clone = PublicResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.confirmation_method)
        pr_kryten = PublicResponse('android', 'K', sentinel.request_type, 'kryten', sentinel.confirmation_method)

        self.assertFalse(pr_rimmer != pr_rimmer)
        self.assertFalse(pr_rimmer != pr_clone)
        self.assertTrue(pr_rimmer != pr_kryten)


class TestSendPasswordResponse(SimpleTestCase):
    """Test `SendPasswordResponse` class."""

    def test_equality(self):
        pr_rimmer = SendPasswordResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.custom_email,
                                         sentinel.confirmation_method)
        pr_clone = SendPasswordResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.custom_email,
                                        sentinel.confirmation_method)
        pr_kryten = SendPasswordResponse('android', 'K', sentinel.request_type, 'kryten', sentinel.other_email,
                                         sentinel.confirmation_method)

        self.assertTrue(pr_rimmer == pr_rimmer)
        self.assertTrue(pr_rimmer == pr_clone)
        self.assertFalse(pr_rimmer == pr_kryten)


class TestPersonalInfoResponse(SimpleTestCase):
    """Test `PersonalInfoResponse` class."""

    def test_equality(self):
        pr_rimmer = PersonalInfoResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.custom_email,
                                         sentinel.confirmation_method)
        pr_clone = PersonalInfoResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.custom_email,
                                        sentinel.confirmation_method)
        pr_kryten = PersonalInfoResponse('android', 'K', sentinel.request_type, 'kryten', sentinel.other_email,
                                         sentinel.confirmation_method)

        self.assertTrue(pr_rimmer == pr_rimmer)
        self.assertTrue(pr_rimmer == pr_clone)
        self.assertFalse(pr_rimmer == pr_kryten)


class TestBlockResponse(SimpleTestCase):
    """Test `BlockResponse` class."""

    def test_equality(self):
        pr_rimmer = BlockResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.action,
                                  sentinel.lock_type, sentinel.confirmation_method)
        pr_clone = BlockResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.action,
                                 sentinel.lock_type, sentinel.confirmation_method)
        pr_kryten = BlockResponse('android', 'K', sentinel.request_type, 'kryten', sentinel.action,
                                  sentinel.lock_type, sentinel.confirmation_method)

        self.assertTrue(pr_rimmer == pr_rimmer)
        self.assertTrue(pr_rimmer == pr_clone)
        self.assertFalse(pr_rimmer == pr_kryten)
