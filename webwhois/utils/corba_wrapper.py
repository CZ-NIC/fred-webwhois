import datetime
import sys

import omniORB
from django.conf import settings
from django.utils import timezone
from pyfco.corba import CorbaNameServiceClient, init_omniorb_exception_handles
from pyfco.corbarecoder import CorbaRecoder

IMPORTED_IDL = []
CORBA_WEBWHOIS = []

init_omniorb_exception_handles(None)

# http://omniorb.sourceforge.net/omnipy3/omniORBpy/omniORBpy004.html
CORBA_ORB = omniORB.CORBA.ORB_init(["-ORBnativeCharCodeSet", "UTF-8"], omniORB.CORBA.ORB_ID)


class WebwhoisCorbaRecoder(CorbaRecoder):
    """
    Decode corba value ccReg/DateTimeType into datetime.datetime with zone.
    Decode corba value ccReg/DateType into datetime.date.
    """

    def _decode_instance(self, value):
        if getattr(value, "_NP_RepositoryId", None) == "IDL:ccReg/DateTimeType:1.0":
            corba_date = timezone.make_aware(datetime.datetime(value.date.year, value.date.month, value.date.day,
                                                               value.hour, value.minute, value.second), timezone.utc)
            if not settings.USE_TZ:
                corba_date = timezone.make_naive(corba_date, timezone.get_default_timezone())
            return corba_date

        if getattr(value, "_NP_RepositoryId", None) == "IDL:ccReg/DateType:1.0":
            return datetime.date(value.year, value.month, value.day)

        result = super(WebwhoisCorbaRecoder, self)._decode_instance(value)

        if getattr(result, "_NP_RepositoryId", None) == "IDL:Registry/Whois/Contact:1.0":
            if result.identification.value.identification_type == "BIRTHDAY" \
                    and result.identification.value.identification_data:
                result.identification.value.identification_data = datetime.datetime.strptime(
                    result.identification.value.identification_data, '%Y-%m-%d').date()
        return result


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
    for idl in settings.WEBWHOIS_CORBA_IDL:
        if idl not in IMPORTED_IDL:
            omniORB.importIDL(idl)
            IMPORTED_IDL.append(idl)

    if CORBA_WEBWHOIS:
        return CORBA_WEBWHOIS[0]

    obj = CorbaNameServiceClient(CORBA_ORB, settings.WEBWHOIS_CORBA_IOR, settings.WEBWHOIS_CORBA_CONTEXT)
    if settings.WEBWHOIS_CORBA_EXPORT_MODULES:
        for name in settings.WEBWHOIS_CORBA_EXPORT_MODULES:
            setattr(obj, name, sys.modules[name])

    CORBA_WEBWHOIS.append(obj)
    return CORBA_WEBWHOIS[0]
