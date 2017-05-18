from django.test import RequestFactory, SimpleTestCase
from django.views.generic import View
from mock import call, patch, sentinel

from webwhois.tests.utils import apply_patch
from webwhois.views.logger_mixin import LoggerMixin


class LoggerView(LoggerMixin, View):

    service_name = "FooService"

    def _get_logging_request_name_and_properties(self, data):
        return self.service_name, data


class TestLoggerMixin(SimpleTestCase):

    def setUp(self):
        self.mock_logger = apply_patch(self, patch('webwhois.views.logger_mixin.LOGGER'))

    def test_prepare_logging_request(self):
        self.mock_logger.create_request.return_value = sentinel.logger_object
        cleaned_data = {"foo": "oof"}
        logger = LoggerView()
        logger.request = RequestFactory().request()
        response = logger.prepare_logging_request(cleaned_data)
        self.assertEqual(response, sentinel.logger_object)
        self.assertEqual(self.mock_logger.mock_calls, [call.create_request('127.0.0.1', 'FooService', 'FooService',
                                                                           properties={'foo': 'oof'})])

    def test_prepare_logging_request_raise_not_implemented(self):
        logger = LoggerMixin()
        with self.assertRaises(NotImplementedError):
            logger.prepare_logging_request({})
        self.assertEqual(self.mock_logger.mock_calls, [])

    def test_finish_logging_request_raise_not_implemented(self):
        logger = LoggerMixin()
        with self.assertRaises(NotImplementedError):
            logger.finish_logging_request()
        self.assertEqual(self.mock_logger.mock_calls, [])
