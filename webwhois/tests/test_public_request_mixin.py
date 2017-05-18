from datetime import datetime

from django.test import SimpleTestCase, override_settings
from django.test.client import RequestFactory
from mock import call, patch

from webwhois.forms import SendPasswordForm
from webwhois.tests.utils import apply_patch
from webwhois.utils.corba_wrapper import REGISTRY_MODULE
from webwhois.views.public_request_mixin import PublicRequestFormView, PublicRequestKnownException, cache


class TestException(Exception):
    "Test exception"


class DebugPublicRequest(PublicRequestFormView):

    public_key = "debug_public_key"

    def __init__(self):
        self.request = RequestFactory().request()

    def _get_logging_request_name_and_properties(self, data):
        return "fooActionName", (("handle", "foo"), )

    def _call_registry_command(self, data, log_request_id):
        return 42


class DebugPublicRequestKnownException(DebugPublicRequest):

    def _call_registry_command(self, data, log_request_id):
        raise PublicRequestKnownException(type(REGISTRY_MODULE.PublicRequest.OBJECT_NOT_FOUND()).__name__)


class DebugPublicRequestRaiseException(DebugPublicRequest):

    def _call_registry_command(self, data, log_request_id):
        raise TestException()


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class TestPublicRequestFormView(SimpleTestCase):

    def setUp(self):
        self.LOGGER = apply_patch(self, patch("webwhois.views.public_request_mixin.LOGGER"))
        apply_patch(self, patch("webwhois.views.logger_mixin.LOGGER", self.LOGGER))
        apply_patch(self, patch("webwhois.views.public_request_mixin.get_random_string", lambda n: "foooo"))

    def tearDown(self):
        cache.clear()

    def test_prepare_logging_request(self):
        pubreq = DebugPublicRequest()
        data = {
            'object_type': 'domain',
            'handle': 'foo.cz',
            'custom_email': 'foo@foo.off',
        }
        logger = pubreq.prepare_logging_request(data)
        self.assertEqual(self.LOGGER.mock_calls, [
            call.create_request('127.0.0.1', 'Public Request', 'fooActionName', properties=(('handle', 'foo'),))
        ])
        self.assertEqual(cache.get(pubreq.public_key), None)
        self.assertEqual(self.LOGGER.create_request.return_value, logger)

    def test_finish_logging_request(self):
        self.LOGGER.result = 'Error'
        pubreq = DebugPublicRequest()
        pubreq.finish_logging_request(self.LOGGER, 42, None)
        self.assertEqual(self.LOGGER.mock_calls, [call.close(properties=[], references=[('publicrequest', 42)])])
        self.assertEqual(self.LOGGER.result, 'Ok')

    def test_finish_logging_request_unexpected_exception(self):
        self.LOGGER.result = 'Error'
        pubreq = DebugPublicRequest()
        pubreq.finish_logging_request(self.LOGGER, None, TestException())
        self.assertEqual(self.LOGGER.mock_calls, [call.close(properties=[('exception', 'TestException')],
                                                             references=[])])
        self.assertEqual(self.LOGGER.result, 'Error')

    def test_finish_logging_request_with_known_exception(self):
        self.LOGGER.result = 'Error'
        pubreq = DebugPublicRequest()
        pubreq.finish_logging_request(self.LOGGER, None, PublicRequestKnownException(
            type(REGISTRY_MODULE.PublicRequest.OBJECT_NOT_FOUND()).__name__))
        self.assertEqual(self.LOGGER.mock_calls, [call.close(properties=[('reason', 'OBJECT_NOT_FOUND')],
                                                             references=[])])
        self.assertEqual(self.LOGGER.result, 'Fail')

    def test_finish_logging_request_no_response_id(self):
        self.LOGGER.result = 'Error'
        pubreq = DebugPublicRequest()
        pubreq.finish_logging_request(self.LOGGER, None, None)
        self.assertEqual(self.LOGGER.mock_calls, [call.close(properties=[], references=[])])
        self.assertEqual(self.LOGGER.result, 'Fail')

    @patch("webwhois.views.public_request_mixin.LOGGER", None)
    @patch("webwhois.views.public_request_mixin.timezone_now")
    def test_logged_call_to_registry_no_logger(self, mock_timezone_now):
        mock_timezone_now.return_value = datetime(2017, 3, 8)
        pubreq = DebugPublicRequest()
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to": "email_in_registry",
        })
        self.assertTrue(form.is_valid())
        pubreq.logged_call_to_registry(form)
        self.assertEqual(cache.get(pubreq.public_key), {
            'handle': 'foo.cz',
            'object_type': 'domain',
            'custom_email': '',
            'confirmation_method': 'signed_email',
            'send_to': 'email_in_registry',
            'response_id': 42,
            'created_date': datetime(2017, 3, 8).date(),
        })
        self.assertEqual(self.LOGGER.mock_calls, [])

    def _init_logger(self):
        self.LOGGER.create_request.return_value.request_id = 42
        self.LOGGER.create_request.return_value.result = 'Error'
        self.LOGGER.create_request.return_value.request_type = 'fooActionName'

    def _get_send_password_form(self, pubreq):
        form = SendPasswordForm({
            "object_type": "domain",
            "handle": "foo.cz",
            "confirmation_method": "signed_email",
            "send_to": "email_in_registry",
        })
        self.assertTrue(form.is_valid())
        return form

    @patch("webwhois.views.public_request_mixin.timezone_now")
    def test_logged_call_to_registry(self, mock_timezone_now):
        mock_timezone_now.return_value = datetime(2017, 3, 8)
        self._init_logger()
        pubreq = DebugPublicRequest()
        form = self._get_send_password_form(pubreq)
        pubreq.logged_call_to_registry(form)
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'fooActionName', properties=(('handle', 'foo'), )),
            call().close(properties=[], references=[('publicrequest', 42)]),
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Ok')
        self.assertEqual(cache.get(pubreq.public_key), {
            'handle': 'foo.cz',
            'object_type': 'domain',
            'request_name': 'fooActionName',
            'custom_email': '',
            'confirmation_method': 'signed_email',
            'send_to': 'email_in_registry',
            'response_id': 42,
            'created_date': datetime(2017, 3, 8).date(),
        })

    def test_logged_call_with_known_exception(self):
        self._init_logger()
        pubreq = DebugPublicRequestKnownException()
        form = self._get_send_password_form(pubreq)
        with self.assertRaises(PublicRequestKnownException):
            pubreq.logged_call_to_registry(form)
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'fooActionName', properties=(('handle', 'foo'), )),
            call().close(properties=[('reason', 'OBJECT_NOT_FOUND')], references=[]),
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Fail')
        self.assertIsNone(cache.get(pubreq.public_key))

    def test_logged_call_raise_exception(self):
        self._init_logger()
        pubreq = DebugPublicRequestRaiseException()
        form = self._get_send_password_form(pubreq)
        with self.assertRaises(TestException):
            pubreq.logged_call_to_registry(form)
        self.assertEqual(self.LOGGER.create_request.mock_calls, [
            call('127.0.0.1', 'Public Request', 'fooActionName', properties=(('handle', 'foo'), )),
            call().close(properties=[('exception', 'TestException')], references=[]),
        ])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Error')
        self.assertIsNone(cache.get(pubreq.public_key))

    def test_raise_not_implemented_error(self):
        self._init_logger()
        pubreq = PublicRequestFormView()
        pubreq.public_key = "foo"
        pubreq.request = RequestFactory().request()
        form = self._get_send_password_form(pubreq)
        with self.assertRaises(NotImplementedError):
            pubreq.logged_call_to_registry(form)
        self.assertEqual(self.LOGGER.create_request.mock_calls, [])
        self.assertEqual(self.LOGGER.create_request.return_value.result, 'Error')
        self.assertIsNone(cache.get(pubreq.public_key))