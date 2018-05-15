# -*- coding: utf-8 -*-
"""Test `webwhois.utils.public_response` module."""
from __future__ import unicode_literals

from datetime import date

import six
from django.test import SimpleTestCase
from mock import patch, sentinel
from testfixtures import Replace, test_date

from webwhois.utils.public_response import BlockResponse, PersonalInfoResponse, PublicResponse, SendPasswordResponse


class TestPublicResponse(SimpleTestCase):
    """Test `PublicResponse` class."""

    def test_create_date_naive(self):
        with self.settings(USE_TZ=False):
            with Replace('webwhois.utils.public_response.date', test_date(2017, 5, 25)):
                public_response = PublicResponse(sentinel.object_type, sentinel.public_request_id,
                                                 sentinel.request_type, sentinel.handle)
        self.assertEqual(public_response.create_date, date(2017, 5, 25))

    def test_create_date_aware(self):
        with self.settings(USE_TZ=True):
            with patch('webwhois.utils.public_response.localdate', return_value=date(2017, 5, 25)):
                public_response = PublicResponse(sentinel.object_type, sentinel.public_request_id,
                                                 sentinel.request_type, sentinel.handle)
        self.assertEqual(public_response.create_date, date(2017, 5, 25))

    def test_repr(self):
        public_response = PublicResponse('smeg_head', 16, sentinel.request_type, 'rimmer')
        self.assertEqual(repr(public_response), '<PublicResponse smeg_head rimmer 16>')

    def test_repr_unicode(self):
        public_response = PublicResponse('ěščř', 16, sentinel.request_type, 'rimmer')
        string = '<PublicResponse ěščř rimmer 16>'
        if six.PY2:
            string = string.encode('utf-8')
        self.assertEqual(repr(public_response), string)

    def test_equality(self):
        pr_rimmer = PublicResponse('smeg_head', 'H', sentinel.request_type, 'rimmer')
        pr_clone = PublicResponse('smeg_head', 'H', sentinel.request_type, 'rimmer')
        pr_kryten = PublicResponse('android', 'K', sentinel.request_type, 'kryten')

        self.assertTrue(pr_rimmer == pr_rimmer)
        self.assertTrue(pr_rimmer == pr_clone)
        self.assertFalse(pr_rimmer == pr_kryten)

    def test_inequality(self):
        pr_rimmer = PublicResponse('smeg_head', 'H', sentinel.request_type, 'rimmer')
        pr_clone = PublicResponse('smeg_head', 'H', sentinel.request_type, 'rimmer')
        pr_kryten = PublicResponse('android', 'K', sentinel.request_type, 'kryten')

        self.assertFalse(pr_rimmer != pr_rimmer)
        self.assertFalse(pr_rimmer != pr_clone)
        self.assertTrue(pr_rimmer != pr_kryten)


class TestSendPasswordResponse(SimpleTestCase):
    """Test `SendPasswordResponse` class."""

    def test_equality(self):
        pr_rimmer = SendPasswordResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.custom_email)
        pr_clone = SendPasswordResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.custom_email)
        pr_kryten = SendPasswordResponse('android', 'K', sentinel.request_type, 'kryten', sentinel.other_email)

        self.assertTrue(pr_rimmer == pr_rimmer)
        self.assertTrue(pr_rimmer == pr_clone)
        self.assertFalse(pr_rimmer == pr_kryten)


class TestPersonalInfoResponse(SimpleTestCase):
    """Test `PersonalInfoResponse` class."""

    def test_equality(self):
        pr_rimmer = PersonalInfoResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.custom_email)
        pr_clone = PersonalInfoResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.custom_email)
        pr_kryten = PersonalInfoResponse('android', 'K', sentinel.request_type, 'kryten', sentinel.other_email)

        self.assertTrue(pr_rimmer == pr_rimmer)
        self.assertTrue(pr_rimmer == pr_clone)
        self.assertFalse(pr_rimmer == pr_kryten)


class TestBlockResponse(SimpleTestCase):
    """Test `BlockResponse` class."""

    def test_equality(self):
        pr_rimmer = BlockResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.action,
                                  sentinel.lock_type)
        pr_clone = BlockResponse('smeg_head', 'H', sentinel.request_type, 'rimmer', sentinel.action,
                                 sentinel.lock_type)
        pr_kryten = BlockResponse('android', 'K', sentinel.request_type, 'kryten', sentinel.action,
                                  sentinel.lock_type)

        self.assertTrue(pr_rimmer == pr_rimmer)
        self.assertTrue(pr_rimmer == pr_clone)
        self.assertFalse(pr_rimmer == pr_kryten)
