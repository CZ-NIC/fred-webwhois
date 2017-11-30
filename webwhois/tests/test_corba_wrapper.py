#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import date, datetime

from django.test import SimpleTestCase, override_settings
from django.utils import timezone
from fred_idl.Registry.PublicRequest import Buffer
from fred_idl.Registry.Whois import WhoisIntf
from mock import call, patch, sentinel
from omniORB import StructBase

from webwhois.utils import CCREG_MODULE
from webwhois.utils.corba_wrapper import CORBA_ORB, WebwhoisCorbaRecoder, load_filemanager_from_idl, \
    load_logger_from_idl, load_whois_from_idl

from .utils import apply_patch


class OtherDateType(StructBase):
    """
    Simulates alternative `DateType` struct.
    """
    _NP_RepositoryId = "IDL:ccReg/DateType:1.0"

    def __init__(self, day, month, year):
        self.day = day
        self.month = month
        self.year = year


class OtherDateTimeType(StructBase):
    """
    Simulates alternative `DateTimeType` struct.
    """
    _NP_RepositoryId = "IDL:ccReg/DateTimeType:1.0"

    def __init__(self, date, hour, minute, second):
        self.date = date
        self.hour = hour
        self.minute = minute
        self.second = second


class TestWebwhoisCorbaRecoder(SimpleTestCase):
    """
    Tests for `WebwhoisCorbaRecoder`.
    """

    def test_decode_date(self):
        raw = CCREG_MODULE.DateType(day=12, month=5, year=2012)
        self.assertEqual(WebwhoisCorbaRecoder().decode(raw), date(2012, 5, 12))

    def test_decode_date_with_zeros(self):
        raw = CCREG_MODULE.DateType(day=0, month=0, year=0)
        self.assertEqual(WebwhoisCorbaRecoder().decode(raw), None)

    def test_other_date_type_class(self):
        raw = OtherDateType(day=12, month=5, year=2012)
        self.assertEqual(WebwhoisCorbaRecoder().decode(raw), date(2012, 5, 12))

    def test_other_date_type_class_with_zeros(self):
        raw = OtherDateType(day=0, month=0, year=0)
        self.assertEqual(WebwhoisCorbaRecoder().decode(raw), None)

    def test_decode_datetime_tz_off(self):
        raw = CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(12, 5, 2012), hour=5, minute=42, second=13)

        with override_settings(USE_TZ=False, TIME_ZONE="Europe/Prague"):
            self.assertEqual(WebwhoisCorbaRecoder().decode(raw), datetime(2012, 5, 12, 7, 42, 13))

    def test_decode_datetime_tz_on(self):
        raw = CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(12, 5, 2012), hour=5, minute=42, second=13)

        with override_settings(USE_TZ=True):
            self.assertEqual(WebwhoisCorbaRecoder().decode(raw), datetime(2012, 5, 12, 5, 42, 13, tzinfo=timezone.utc))

    def test_other_date_time_type_class(self):
        raw = OtherDateTimeType(date=OtherDateType(12, 5, 2012), hour=5, minute=42, second=13)
        with override_settings(USE_TZ=True):
            self.assertEqual(WebwhoisCorbaRecoder().decode(raw), datetime(2012, 5, 12, 5, 42, 13, tzinfo=timezone.utc))

    def test_decode_datetime_with_zeros(self):
        raw = CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(0, 0, 0), hour=0, minute=0, second=0)
        self.assertEqual(WebwhoisCorbaRecoder().decode(raw), None)

    def test_other_datetime_type_class_with_zeros(self):
        raw = OtherDateTimeType(date=OtherDateType(0, 0, 0), hour=0, minute=0, second=0)
        self.assertEqual(WebwhoisCorbaRecoder().decode(raw), None)

    def test_decode_buffer(self):
        buffer_obj = Buffer('foo')
        self.assertEqual(WebwhoisCorbaRecoder().decode(buffer_obj), 'foo')

    def test_decode_file_download(self):
        file_download = CCREG_MODULE._objref_FileDownload()
        self.assertEqual(WebwhoisCorbaRecoder().decode(file_download), file_download)

    def test_encode_file_download(self):
        file_download = CCREG_MODULE._objref_FileDownload()
        self.assertEqual(WebwhoisCorbaRecoder().encode(file_download), file_download)


class TestLoadIdl(SimpleTestCase):

    def setUp(self):
        patcher = patch('webwhois.utils.corba_wrapper._CLIENT')
        self.corba_mock = apply_patch(self, patcher)
        self.corba_mock.get_object.return_value = sentinel.corba_object

    def test_load_whois_from_idl(self):
        result = load_whois_from_idl()

        self.assertEqual(result, sentinel.corba_object)
        self.assertEqual(self.corba_mock.mock_calls, [call.get_object('Whois2', WhoisIntf)])

    def test_load_filemanager_from_idl(self):
        result = load_filemanager_from_idl()

        self.assertEqual(result, sentinel.corba_object)
        self.assertEqual(self.corba_mock.mock_calls,
                         [call.get_object('FileManager', CCREG_MODULE.FileManager)])

    @override_settings(WEBWHOIS_LOGGER_CORBA_IOR='localhost', WEBWHOIS_LOGGER_CORBA_CONTEXT='fred')
    @patch('webwhois.utils.corba_wrapper.CorbaNameServiceClient')
    def test_load_logger_from_idl(self, mock_client):
        result = load_logger_from_idl()
        self.assertEqual(mock_client.mock_calls, [
            call(CORBA_ORB, 'localhost', 'fred'),
            call().get_object('Logger', CCREG_MODULE.Logger),
        ])
        self.assertEqual(result, mock_client().get_object())
