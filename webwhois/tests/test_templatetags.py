from django.test import SimpleTestCase

from webwhois.templatetags.webwhois_filters import contact_ssn_type_label, text_wrap


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
