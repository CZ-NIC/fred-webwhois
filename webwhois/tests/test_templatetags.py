#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from webwhois.templatetags.keyset_filters import dnskey_alg_label, dnskey_flag_labels
from webwhois.templatetags.webwhois_filters import add_scheme, contact_ssn_type_label, idn_decode, strip_scheme, \
    text_wrap


class TestTemplateTags(SimpleTestCase):

    def test_text_wrap(self):
        self.assertEqual(text_wrap('0123456789012345678901234', 6), '012345\n678901\n234567\n890123\n4')
        with self.assertRaises(AttributeError):
            text_wrap(None, 3)
        self.assertEqual(text_wrap('', 3), '')

    def test_contact_ssn_type_label(self):
        for code, label in (
                            ('RC', 'Birth date'),
                            ('OP', 'Personal ID'),
                            ('PASS', 'Passport number'),
                            ('ICO', 'VAT ID number'),
                            ('MPSV', 'MPSV ID'),
                            ('BIRTHDAY', 'Birth day'),
                            ('foo', 'Unspecified type: foo'),
                            ('', ''),
                           ):
            self.assertEqual(contact_ssn_type_label(code), label)

    def test_idn_decode(self):
        self.assertEqual(idn_decode("fred.cz"), "fred.cz")
        self.assertEqual(idn_decode("xn--hkyrky-ptac70bc.cz"), u"háčkyčárky.cz")
        self.assertEqual(idn_decode("."), ".")

    def test_add_scheme(self):
        self.assertEqual(add_scheme("www.nic.cz"), "http://www.nic.cz")
        self.assertEqual(add_scheme("http://www.nic.cz"), "http://www.nic.cz")
        self.assertEqual(add_scheme("https://www.nic.cz"), "https://www.nic.cz")

    def test_strip_scheme(self):
        self.assertEqual(strip_scheme("www.nic.cz"), "www.nic.cz")
        self.assertEqual(strip_scheme("http://www.nic.cz"), "www.nic.cz")
        self.assertEqual(strip_scheme("https://www.nic.cz"), "www.nic.cz")

    def test_dnskey_alg_label(self):
        self.assertEqual(dnskey_alg_label(0), "Delete DS")
        self.assertEqual(dnskey_alg_label(8), "RSA/SHA-256")
        self.assertEqual(dnskey_alg_label(17), "Unassigned")
        self.assertEqual(dnskey_alg_label(122), "Unassigned")
        self.assertEqual(dnskey_alg_label(123), "Reserved")
        self.assertEqual(dnskey_alg_label(251), "Reserved")

    def test_dnskey_alg_label_invalid_key(self):
        with self.assertRaisesMessage(ValueError, 'dnskey_alg_label: alg_id -1 is out of range.'):
            dnskey_alg_label(-1)
        with self.assertRaisesMessage(ValueError, 'dnskey_alg_label: alg_id 257 is out of range.'):
            dnskey_alg_label(257)

    def test_dnskey_flag_labels(self):
        self.assertEqual(dnskey_flag_labels(0), "")
        self.assertEqual(dnskey_flag_labels(0b1000000000000000), "")
        self.assertEqual(dnskey_flag_labels(0b0100000000000000), "")
        self.assertEqual(dnskey_flag_labels(0b0010000000000000), "")
        self.assertEqual(dnskey_flag_labels(0b0001000000000000), "")
        self.assertEqual(dnskey_flag_labels(0b0000100000000000), "")
        self.assertEqual(dnskey_flag_labels(0b0000010000000000), "")
        self.assertEqual(dnskey_flag_labels(0b0000001000000000), "")
        self.assertEqual(dnskey_flag_labels(0b0000000100000000), "ZONE")
        self.assertEqual(dnskey_flag_labels(0b0000000010000000), "REVOKE")
        self.assertEqual(dnskey_flag_labels(0b0000000001000000), "")
        self.assertEqual(dnskey_flag_labels(0b0000000000100000), "")
        self.assertEqual(dnskey_flag_labels(0b0000000000010000), "")
        self.assertEqual(dnskey_flag_labels(0b0000000000001000), "")
        self.assertEqual(dnskey_flag_labels(0b0000000000000100), "")
        self.assertEqual(dnskey_flag_labels(0b0000000000000010), "")
        self.assertEqual(dnskey_flag_labels(0b0000000000000001), "Secure Entry Point (SEP)")
        self.assertEqual(dnskey_flag_labels(0b0000000110000001), "ZONE, REVOKE, Secure Entry Point (SEP)")

    def test_dnskey_flag_labels_invalid_key(self):
        with self.assertRaisesMessage(ValueError, 'dnskey_flag_labels: flags -1 is out of range.'):
            dnskey_flag_labels(-1)
        with self.assertRaisesMessage(ValueError, 'dnskey_flag_labels: flags 65536 is out of range.'):
            dnskey_flag_labels(0b10000000000000000)
