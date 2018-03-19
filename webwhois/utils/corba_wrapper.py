"""Utilities for Corba."""
from __future__ import unicode_literals

import datetime

import omniORB
from django.conf import settings
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from fred_idl import ccReg
from fred_idl.ccReg import FileManager, Logger
from fred_idl.Registry import Buffer, IsoDate, IsoDateTime, PublicRequest, RecordStatement, Whois
from pyfco import CorbaClient, CorbaClientProxy
from pyfco.corba import CorbaNameServiceClient, init_omniorb_exception_handles
from pyfco.corbarecoder import CorbaRecoder
from pyfco.recoder import decode_iso_date, decode_iso_datetime

from webwhois.settings import WEBWHOIS_LOGGER, WEBWHOIS_SETTINGS

from .logger import create_logger


class WebwhoisCorbaRecoder(CorbaRecoder):
    """
    Decodes whois specific structures.

    Decodes corba structure `ccReg.DateTimeType` into datetime.datetime with zone.
    Decodes corba structure `ccReg/DateType` into datetime.date.
    Decodes contact identifiers to datetime.date if it is a birthday.
    Decodes IDL:Registry/PublicRequest/Buffer:1.0. into bytes.
    Decodes IDL:Registry/RecordStatement/PdfBuffer:1.0. into bytes.
    """

    def __init__(self, coding='ascii'):
        super(WebwhoisCorbaRecoder, self).__init__(coding)
        self.add_recode_function(Buffer, self._decode_buffer, self._identity)
        self.add_recode_function(ccReg._objref_FileDownload, self._identity, self._identity)
        self.add_recode_function(IsoDate, decode_iso_date, self._identity)
        self.add_recode_function(IsoDateTime, self._decode_iso_datetime, self._identity)

    def _decode_buffer(self, value):
        """Decode `Registry.Buffer` struct into bytes."""
        return value.data

    def _decode_struct(self, value):
        # Dynamic loading of IDL with includes causes problems with classes. The same class may appear in several
        # entities, so type matching can not be used.
        struct_ident = getattr(value, "_NP_RepositoryId")
        if struct_ident == "IDL:ccReg/DateTimeType:1.0":
            if value.date.year == 0 and value.date.month == 0 and value.date.day == 0 and value.hour == 0 and \
                    value.minute == 0 and value.second == 0:
                return None
            corba_date = timezone.make_aware(datetime.datetime(value.date.year, value.date.month, value.date.day,
                                                               value.hour, value.minute, value.second), timezone.utc)
            if not settings.USE_TZ:
                corba_date = timezone.make_naive(corba_date, timezone.get_default_timezone())
            return corba_date
        elif struct_ident == "IDL:ccReg/DateType:1.0":
            if value.year == 0 and value.month == 0 and value.day == 0:
                return None
            return datetime.date(value.year, value.month, value.day)
        else:
            return super(WebwhoisCorbaRecoder, self)._decode_struct(value)

    def _decode_iso_datetime(self, value):
        """Decode `IsoDateTime` struct to datetime object with respect to the timezone settings."""
        result = decode_iso_datetime(value)
        if not settings.USE_TZ:
            result = timezone.make_naive(result, timezone.get_default_timezone())
        return result


init_omniorb_exception_handles(None)

# http://omniorb.sourceforge.net/omnipy3/omniORBpy/omniORBpy004.html
CORBA_ORB = omniORB.CORBA.ORB_init([b"-ORBnativeCharCodeSet", b"UTF-8"], omniORB.CORBA.ORB_ID)
_CLIENT = CorbaNameServiceClient(CORBA_ORB, WEBWHOIS_SETTINGS.CORBA_NETLOC, WEBWHOIS_SETTINGS.CORBA_CONTEXT)


def load_whois_from_idl():
    return _CLIENT.get_object('Whois2', Whois.WhoisIntf)


def load_public_request_from_idl():
    return _CLIENT.get_object('PublicRequest', PublicRequest.PublicRequestIntf)


def load_filemanager_from_idl():
    return _CLIENT.get_object('FileManager', FileManager)


def load_record_statement():
    return _CLIENT.get_object('RecordStatement', RecordStatement.Server)


def load_logger_from_idl():
    service_client = CorbaNameServiceClient(CORBA_ORB, WEBWHOIS_SETTINGS.LOGGER_CORBA_NETLOC,
                                            WEBWHOIS_SETTINGS.LOGGER_CORBA_CONTEXT)
    return CorbaClient(service_client.get_object('Logger', Logger), CorbaRecoder('utf-8'),
                       ccReg.Logger.INTERNAL_SERVER_ERROR)


_WHOIS = SimpleLazyObject(load_whois_from_idl)
_PUBLIC_REQUEST = SimpleLazyObject(load_public_request_from_idl)
_FILE_MANAGER = SimpleLazyObject(load_filemanager_from_idl)
_RECORD_STATEMENT = SimpleLazyObject(load_record_statement)

if WEBWHOIS_LOGGER:
    LOGGER = SimpleLazyObject(lambda: create_logger(WEBWHOIS_LOGGER, load_logger_from_idl(), ccReg))
else:
    LOGGER = None

WHOIS = CorbaClientProxy(CorbaClient(_WHOIS, WebwhoisCorbaRecoder('utf-8'), Whois.INTERNAL_SERVER_ERROR))
PUBLIC_REQUEST = CorbaClientProxy(CorbaClient(_PUBLIC_REQUEST, WebwhoisCorbaRecoder('utf-8'),
                                              PublicRequest.INTERNAL_SERVER_ERROR))
FILE_MANAGER = CorbaClientProxy(CorbaClient(_FILE_MANAGER, WebwhoisCorbaRecoder('utf-8'), FileManager.InternalError))
RECORD_STATEMENT = CorbaClientProxy(CorbaClient(_RECORD_STATEMENT, WebwhoisCorbaRecoder('utf-8'),
                                                RecordStatement.INTERNAL_SERVER_ERROR))
