from django.test import SimpleTestCase
from django.test.utils import override_settings
from mock import call, patch, sentinel

from webwhois.utils import CCREG_MODULE, WHOIS_MODULE
from webwhois.utils.corba_wrapper import CorbaWrapper
from webwhois.views.pages import CORBA_ORB, load_filemanager_from_idl, load_logger_from_idl, load_whois_from_idl

from .utils import apply_patch


class TestLoadIdl(SimpleTestCase):

    def setUp(self):
        patcher = patch('webwhois.views.pages._CLIENT')
        self.corba_mock = apply_patch(self, patcher)
        self.corba_mock.get_object.return_value = sentinel.corba_object

    def test_load_whois_from_idl(self):
        wrapper = load_whois_from_idl()

        self.assertIsInstance(wrapper, CorbaWrapper)
        self.assertEqual(wrapper.corba_object, sentinel.corba_object)
        self.assertEqual(self.corba_mock.mock_calls, [call.get_object('Whois2', WHOIS_MODULE.WhoisIntf)])

    def test_load_filemanager_from_idl(self):
        result = load_filemanager_from_idl()

        self.assertEqual(result, sentinel.corba_object)
        self.assertEqual(self.corba_mock.mock_calls,
                         [call.get_object('FileManager', CCREG_MODULE.FileManager)])

    @override_settings(WEBWHOIS_LOGGER_CORBA_IOR='localhost', WEBWHOIS_LOGGER_CORBA_CONTEXT='fred')
    @patch('webwhois.views.pages.CorbaNameServiceClient')
    def test_load_logger_from_idl(self, mock_client):
        result = load_logger_from_idl()
        self.assertEqual(mock_client.mock_calls, [
            call(CORBA_ORB, 'localhost', 'fred'),
            call().get_object('Logger', CCREG_MODULE.Logger),
        ])
        self.assertEqual(result, mock_client().get_object())
