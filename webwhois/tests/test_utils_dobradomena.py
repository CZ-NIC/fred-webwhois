from __future__ import unicode_literals

import os

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings
from mock import patch

from webwhois.tests.utils import apply_patch, prepare_mkdtemp
from webwhois.utils.dobradomena import get_dobradomena_list


@patch('webwhois.utils.dobradomena.WEBWHOIS_DOBRADOMENA_FILE_NAME', 'manual.pdf')
@patch('webwhois.utils.dobradomena.WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN', '/%(handle)s/%(lang)s/')
class TestDobradomena(SimpleTestCase):

    def setUp(self):
        super(TestDobradomena, self).setUp()
        self.tmp_folder_name = prepare_mkdtemp(self)
        apply_patch(self, patch('webwhois.utils.dobradomena.WEBWHOIS_DOBRADOMENA_ROOT', self.tmp_folder_name))

    def test_dir_missing(self):
        with override_settings(WEBWHOIS_DOBRADOMENA_ROOT=self.tmp_folder_name + "foo"):
            self.assertEqual(get_dobradomena_list("en"), {})

    def test_file(self):
        os.mkdir(os.path.join(self.tmp_folder_name, "www"))
        path = os.path.join(self.tmp_folder_name, "foo", "en")
        os.makedirs(path)
        os.mknod(os.path.join(path, "manual.pdf"))
        self.assertEqual(get_dobradomena_list("EN"), {'REG-FOO': '/foo/en/manual.pdf'})

    def test_no_file(self):
        path = os.path.join(self.tmp_folder_name, "foo", "en")
        os.makedirs(path)
        self.assertEqual(get_dobradomena_list("en"), {})


@patch('webwhois.utils.dobradomena.WEBWHOIS_DOBRADOMENA_FILE_NAME', None)
@patch('webwhois.utils.dobradomena.WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN', None)
class TestConfigInvalid(SimpleTestCase):

    def setUp(self):
        super(TestConfigInvalid, self).setUp()
        self.tmp_folder_name = prepare_mkdtemp(self)
        apply_patch(self, patch('webwhois.utils.dobradomena.WEBWHOIS_DOBRADOMENA_ROOT', self.tmp_folder_name))

    def test_no_root(self):
        apply_patch(self, patch('webwhois.utils.dobradomena.WEBWHOIS_DOBRADOMENA_ROOT', None))
        self.assertEqual(get_dobradomena_list("en"), {})

    def test_missing_file_name(self):
        os.mkdir(os.path.join(self.tmp_folder_name, "foo"))
        with self.assertRaisesRegexp(ImproperlyConfigured, "WEBWHOIS_DOBRADOMENA_ROOT is set but "
                                     "WEBWHOIS_DOBRADOMENA_FILE_NAME missing."):
            get_dobradomena_list("en")

    def test_missing_manual_url_pattern(self):
        apply_patch(self, patch('webwhois.utils.dobradomena.WEBWHOIS_DOBRADOMENA_FILE_NAME', 'manual.pdf'))
        path = os.path.join(self.tmp_folder_name, "foo", "en")
        os.makedirs(path)
        os.mknod(os.path.join(path, "manual.pdf"))
        with self.assertRaisesRegexp(ImproperlyConfigured, "WEBWHOIS_DOBRADOMENA_ROOT is set but "
                                     "WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN missing."):
            get_dobradomena_list("en")
