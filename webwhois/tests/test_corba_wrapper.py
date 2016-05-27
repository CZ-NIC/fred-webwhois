from datetime import date, datetime

from django.test import SimpleTestCase, override_settings
from django.utils import timezone
from omniORB import StructBase

from webwhois.utils import CCREG_MODULE, WHOIS_MODULE
from webwhois.utils.corba_wrapper import WebwhoisCorbaRecoder


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

    def test_other_date_type_class(self):
        raw = OtherDateType(day=12, month=5, year=2012)
        self.assertEqual(WebwhoisCorbaRecoder().decode(raw), date(2012, 5, 12))

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
