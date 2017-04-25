"""
Utilities for Corba.
"""
import datetime

import omniORB
from django.conf import settings
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from pyfco.corba import CorbaNameServiceClient, init_omniorb_exception_handles
from pyfco.corbarecoder import CorbaRecoder

from webwhois.settings import WEBWHOIS_CORBA_CONTEXT, WEBWHOIS_CORBA_IDL, WEBWHOIS_CORBA_IOR, WEBWHOIS_LOGGER, \
    WEBWHOIS_LOGGER_CORBA_CONTEXT, WEBWHOIS_LOGGER_CORBA_IOR

from .logger import create_logger


def _import_idl():
    for idl in WEBWHOIS_CORBA_IDL:
        omniORB.importIDL(idl)


def _get_registry_module():
    """
    Returns `Registry` module.
    """
    try:
        from Registry import Whois, PublicRequest
        import Registry
    except ImportError:
        _import_idl()
        from Registry import Whois, PublicRequest
        import Registry
    assert Whois
    assert PublicRequest
    return Registry


def _get_ccreg_module():
    """
    Returns `ccReg` module.
    """
    try:
        import ccReg
    except ImportError:
        _import_idl()
        import ccReg
    return ccReg


REGISTRY_MODULE = SimpleLazyObject(_get_registry_module)
CCREG_MODULE = SimpleLazyObject(_get_ccreg_module)


class WebwhoisCorbaRecoder(CorbaRecoder):
    """
    Decodes whois specific structures.

    Decodes corba structure `ccReg.DateTimeType` into datetime.datetime with zone.
    Decodes corba structure `ccReg/DateType` into datetime.date.
    Decodes contact identifiers to datetime.date if it is a birthday.
    Decodes IDL:Registry/PublicRequest/Buffer:1.0. into bytes.
    """

    def __init__(self, coding='ascii'):
        super(WebwhoisCorbaRecoder, self).__init__(coding)
        self.add_recode_function(REGISTRY_MODULE.PublicRequest.Buffer, self._decode_buffer, self._identity)

    def _decode_buffer(self, value):
        return value.value  # IDL:Registry/PublicRequest/Buffer:1.0

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


class CorbaWrapper(object):
    """
    Client for object of CORBA interface.
    """

    def __init__(self, corba_object):
        self.corba_object = corba_object
        self.recoder = WebwhoisCorbaRecoder("utf-8")

    def _call_method(self, method_name, *args):
        """
        Utility method that actually performs the Corba call.
        """
        args = self.recoder.encode(args)
        result = getattr(self.corba_object, method_name)(*args)
        return self.recoder.decode(result)

    def __getattr__(self, name):
        """
        Call CORBA object methods.
        """
        if hasattr(self.corba_object, name):
            def wrapper(*args):
                return self._call_method(name, *args)
            return wrapper
        raise AttributeError


init_omniorb_exception_handles(None)

# http://omniorb.sourceforge.net/omnipy3/omniORBpy/omniORBpy004.html
CORBA_ORB = omniORB.CORBA.ORB_init(["-ORBnativeCharCodeSet", "UTF-8"], omniORB.CORBA.ORB_ID)
_CLIENT = CorbaNameServiceClient(CORBA_ORB, WEBWHOIS_CORBA_IOR, WEBWHOIS_CORBA_CONTEXT)


def load_whois_from_idl():
    return CorbaWrapper(_CLIENT.get_object('Whois2', REGISTRY_MODULE.Whois.WhoisIntf))


def load_public_request_from_idl():
    return CorbaWrapper(_CLIENT.get_object('PublicRequest', REGISTRY_MODULE.PublicRequest.PublicRequestIntf))


def load_filemanager_from_idl():
    return _CLIENT.get_object('FileManager', CCREG_MODULE.FileManager)


def load_logger_from_idl():
    service_client = CorbaNameServiceClient(CORBA_ORB, WEBWHOIS_LOGGER_CORBA_IOR, WEBWHOIS_LOGGER_CORBA_CONTEXT)
    return service_client.get_object('Logger', CCREG_MODULE.Logger)


WHOIS = SimpleLazyObject(load_whois_from_idl)
PUBLIC_REQUEST = SimpleLazyObject(load_public_request_from_idl)
FILEMANAGER = SimpleLazyObject(load_filemanager_from_idl)
if WEBWHOIS_LOGGER:
    LOGGER = SimpleLazyObject(lambda: create_logger(WEBWHOIS_LOGGER, load_logger_from_idl(), CCREG_MODULE))
else:
    LOGGER = None
