import unicodedata

from django.test import SimpleTestCase

from webwhois.forms.fields import RemoveWhitespacesField


class TestFields(SimpleTestCase):

    def test_remove_whitespaces_field(self):
        field = RemoveWhitespacesField()
        self.assertEqual(field.to_python("foo"), "foo")
        self.assertEqual(field.to_python(" foo "), "foo")
        self.assertEqual(field.to_python(" foo foo "), "foo foo")
        self.assertEqual(field.to_python("\t foo \n"), "foo")

        for name in ('EM QUAD',
                     'EM SPACE',
                     'EN QUAD',
                     'EN SPACE',
                     'FIGURE SPACE',
                     'FOUR-PER-EM SPACE',
                     'HAIR SPACE',
                     'IDEOGRAPHIC SPACE',
                     'MEDIUM MATHEMATICAL SPACE',
                     'NARROW NO-BREAK SPACE',
                     'NO-BREAK SPACE',
                     'PUNCTUATION SPACE',
                     'SIX-PER-EM SPACE',
                     'THIN SPACE',
                     'THREE-PER-EM SPACE',
                     # Following unicodes are in category "Cf" (Other format), not "Zs" (Separator, Space).
                     # 'ZERO WIDTH NO-BREAK SPACE',
                     # 'ZERO WIDTH SPACE',
                     ):
            space = {"space": unicodedata.lookup(name)}
            self.assertEqual(field.to_python("%(space)sfoo%(space)s" % space), "foo")
