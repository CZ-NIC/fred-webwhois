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

CORBA_WEBWHOIS = []

init_omniorb_exception_handles(None)

# http://omniorb.sourceforge.net/omnipy3/omniORBpy/omniORBpy004.html
CORBA_ORB = omniORB.CORBA.ORB_init(["-ORBnativeCharCodeSet", "UTF-8"], omniORB.CORBA.ORB_ID)


def _import_idl():
    for idl in settings.WEBWHOIS_CORBA_IDL:
        omniORB.importIDL(idl)


def _get_whois_module():
    """
    Returns `Registry.Whois` module.
    """
    try:
        from Registry import Whois
    except ImportError:
        _import_idl()
        from Registry import Whois
    return Whois


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


WHOIS_MODULE = SimpleLazyObject(_get_whois_module)
CCREG_MODULE = SimpleLazyObject(_get_ccreg_module)


class WebwhoisCorbaRecoder(CorbaRecoder):
    """
    Decodes whois specific structures.

    Decodes corba structure `ccReg.DateTimeType` into datetime.datetime with zone.
    Decodes corba structure `ccReg/DateType` into datetime.date.
    Decodes contact identifiers to datetime.date if it is a birthday.
    """
    def _decode_struct(self, value):
        # Dynamic loading of IDL with includes causes problems with classes. The same class may appear in several
        # entities, so type matching can not be used.
        struct_ident = getattr(value, "_NP_RepositoryId")
        if struct_ident == "IDL:ccReg/DateTimeType:1.0":
            corba_date = timezone.make_aware(datetime.datetime(value.date.year, value.date.month, value.date.day,
                                                               value.hour, value.minute, value.second), timezone.utc)
            if not settings.USE_TZ:
                corba_date = timezone.make_naive(corba_date, timezone.get_default_timezone())
            return corba_date
        elif struct_ident == "IDL:ccReg/DateType:1.0":
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


def get_corba_for_module():
    """
    Import IDL and create Corba object for a module.
    """
    if CORBA_WEBWHOIS:
        return CORBA_WEBWHOIS[0]

    obj = CorbaNameServiceClient(CORBA_ORB, settings.WEBWHOIS_CORBA_IOR, settings.WEBWHOIS_CORBA_CONTEXT)

    CORBA_WEBWHOIS.append(obj)
    return CORBA_WEBWHOIS[0]
