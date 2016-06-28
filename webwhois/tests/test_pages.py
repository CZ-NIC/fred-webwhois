from django.test import SimpleTestCase
from mock import call, patch, sentinel

from webwhois.utils import CCREG_MODULE, WHOIS_MODULE
from webwhois.utils.corba_wrapper import CorbaWrapper
from webwhois.views.pages import load_filemanager_from_idl, load_whois_from_idl

from .utils import apply_patch


class TestLoadIdl(SimpleTestCase):
    def setUp(self):
        patcher = patch('webwhois.views.pages.get_corba_for_module')
        self.corba_mock = apply_patch(self, patcher)
        self.corba_mock.return_value.get_object.return_value = sentinel.corba_object

    def test_load_whois_from_idl(self):
        wrapper = load_whois_from_idl()

        self.assertIsInstance(wrapper, CorbaWrapper)
        self.assertEqual(wrapper.corba_object, sentinel.corba_object)
        self.assertEqual(self.corba_mock.mock_calls, [call(), call().get_object('Whois2', WHOIS_MODULE.WhoisIntf)])

    def test_load_filemanager_from_idl(self):
        result = load_filemanager_from_idl()

        self.assertEqual(result, sentinel.corba_object)
        self.assertEqual(self.corba_mock.mock_calls,
                         [call(), call().get_object('FileManager', CCREG_MODULE.FileManager)])
