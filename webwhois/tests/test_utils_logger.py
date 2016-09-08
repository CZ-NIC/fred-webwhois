from django.test import SimpleTestCase
from mock import MagicMock, Mock, call
from pylogger.corbalogger import Logger

from webwhois.utils.logger import create_logger


class TestLogger(SimpleTestCase):

    def test_create_logger(self):
        with self.assertRaisesRegexp(ImportError, "foo doesn't look like a module path"):
            create_logger("foo", None, None)
        with self.assertRaisesRegexp(ImportError, "No module named foo"):
            create_logger("foo.off", None, None)
        with self.assertRaisesRegexp(ImportError, 'Module "pylogger.foo" does not define a "foo" attribute/class'):
            create_logger("pylogger.foo", None, None)

        corba, ccreg = MagicMock(), Mock()
        corba.getServices.return_value = []
        response = create_logger("pylogger.corbalogger.Logger", corba, ccreg)
        self.assertIsInstance(response, Logger)
        self.assertEqual(ccreg.mock_calls, [])
        self.assertEqual(corba.mock_calls, [call.getServices()])
