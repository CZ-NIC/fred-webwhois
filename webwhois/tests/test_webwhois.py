from django.test import SimpleTestCase
from django.test.client import Client
from django.test.utils import override_settings

from webwhois.views import *
from webwhois.utils.corbarecoder import c2u




@override_settings(CORBA_MOCK=True, CAPTCHA_MAX_REQUESTS=1000)
class TestDetailViews(SimpleTestCase):

    def setUp(self):
        self.c = Client()
        self._WHOIS = WhoisIntfMock()

    def test_get_contact(self):
        res = self.c.get("/contact/KONTAKT")
        exp = c2u(self._WHOIS.get_contact_by_handle(u"KONTAKT"))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['data'].handle, exp.handle)

    def test_notfound_contact(self):
        res = self.c.get("/contact/NOT_FOUND")

        self.assertNotIn('data', res.context)
        self.assertEqual(res.context['error'], 'not_found')

    def test_get_domain(self):
        res = self.c.get("/domain/fred.cz")
        exp = c2u(self._WHOIS.get_domain_by_handle(u"fred.cz"))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['data'].handle, exp.handle)

    def test_notfound_domain(self):
        res = self.c.get("/domain/notfound.cz")

        self.assertNotIn('data', res.context)
        self.assertEqual(res.context['error'], 'not_found')

    def test_invalid_domain(self):
        res = self.c.get("/domain/invalid")

        self.assertNotIn('data', res.context)
        self.assertEqual(res.context['error'], 'invalid_label')

    def test_many_labels_domain(self):
        res = self.c.get("/domain/many.labels.cz")

        self.assertNotIn('data', res.context)
        self.assertEqual(res.context['error'], 'too_many_labels')

    def test_unmanaged_zone_domain(self):
        res = self.c.get("/domain/unmanaged.zone")

        self.assertNotIn('data', res.context)
        self.assertEqual(res.context['error'], 'unmanaged_zone')

    def test_get_nsset(self):
        res = self.c.get("/nsset/NSSET-1")
        exp = c2u(self._WHOIS.get_nsset_by_handle(u"NSSET-1"))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['data'].handle, exp.handle)

    def test_notfound_nsset(self):
        res = self.c.get("/nsset/NOT_FOUND")

        self.assertNotIn('data', res.context)
        self.assertEqual(res.context['error'], 'not_found')

    def test_get_keyset(self):
        res = self.c.get("/keyset/KEYSID-1")
        exp = c2u(self._WHOIS.get_keyset_by_handle(u"KEYSID-1"))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['data'].handle, exp.handle)

    def test_notfound_keyset(self):
        res = self.c.get("/keyset/NOT_FOUND")

        self.assertNotIn('data', res.context)
        self.assertEqual(res.context['error'], 'not_found')

    def test_get_registrar(self):
        res = self.c.get("/registrar/REG-FRED_B")
        exp = c2u(self._WHOIS.get_registrar_by_handle(u"REG-FRED_B"))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['data'].handle, exp.handle)

    def test_notfound_registrar(self):
        res = self.c.get("/registrar/NOT_FOUND")

        self.assertNotIn('data', res.context)
        self.assertEqual(res.context['error'], 'not_found')


@override_settings(CORBA_MOCK=True, CAPTCHA_MAX_REQUESTS=1000)
class TestQuery(SimpleTestCase):

    def setUp(self):
        self.c = Client()

    def test_contact_query(self):
        res = self.c.post("/", {"handle": "KONTAKT"})
        self.assertRedirects(res, '/contact/KONTAKT')

    def test_domain_query(self):
        res = self.c.post("/", {"handle": "fred.cz"})
        self.assertRedirects(res, '/domain/fred.cz')

    def test_nsset_query(self):
        res = self.c.post("/", {"handle": "NSSET-1"})
        self.assertRedirects(res, '/nsset/NSSET-1')

    def test_registrar_query(self):
        res = self.c.post("/", {"handle": "REG-FRED_B"})
        self.assertRedirects(res, '/registrar/REG-FRED_B')

    def test_duplicity_query(self):
        res = self.c.post("/", {"handle": "KEYSID-1"})
        self.assertInHTML("""<a href="/keyset/KEYSID-1">KEYSID-1</a>""", res.content)
        self.assertInHTML("""<a href="/contact/KEYSID-1">KEYSID-1</a>""", res.content)


@override_settings(CORBA_MOCK=True, CAPTCHA_MAX_REQUESTS=1000)
class TestRegistrars(SimpleTestCase):

    def setUp(self):
        self.c = Client()
        self._WHOIS = WhoisIntfMock()

    def test_registrars_retail(self):
        res = self.c.get("/registrars/")
        self.assertEqual(res.status_code, 200)
        groups = self._WHOIS.get_registrar_groups()
        group = []
        for g in groups:
            if g.name == 'certified':
                group = g.members
                break
        self.assertEqual(len(res.context['data']), len(group))

    def test_registrars_wholesale(self):
        res = self.c.get("/registrars/wholesale")
        self.assertEqual(res.status_code, 200)
        groups = self._WHOIS.get_registrar_groups()
        group = []
        for g in groups:
            if g.name == 'uncertified':
                group = g.members
                break
        self.assertEqual(len(res.context['data']), len(group))

    def test_cert_eval_file(self):
        res = self.c.get("/registrar/REG-FRED_B/download_eval")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, 'test\n')

@override_settings(CORBA_MOCK=True, CAPTCHA_MAX_REQUESTS=2)
class TestCaptcha(SimpleTestCase):

    def setUp(self):
        self.c = Client()

    def test_captcha(self):
        res1 = self.c.post("/", {"handle": "REG-FRED_B"}, follow=True)
        res2 = self.c.post("/", {"handle": "REG-FRED_B"}, follow=True)
        res3 = self.c.post("/", {"handle": "REG-FRED_B"}, follow=True)
        self.assertIsNotNone(res1.context['data'])
        self.assertIsNotNone(res2.context['data'])
        self.assertEqual(isinstance(res3.context['form'], QueryCaptchaForm), True)
