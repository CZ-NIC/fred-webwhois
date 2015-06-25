#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

import omniORB
import CosNaming
from omniORB import CORBA


def transientFailure(cookie, retries, exc):
    if retries > 10:
        return False
    else:
        return True

def commFailure(cookie, retries, exc):
    if retries > 20:
        return False
    else:
        return True

def systemFailure(cookie, retries, exc):
    if retries > 5:
        return False
    else:
        return True


cookie = None
omniORB.installTransientExceptionHandler(cookie, transientFailure)
omniORB.installCommFailureExceptionHandler(cookie, commFailure)
omniORB.installSystemExceptionHandler(cookie, systemFailure)


# http://omniorb.sourceforge.net/omnipy3/omniORBpy/omniORBpy004.html
#["-ORBnativeCharCodeSet", "UTF-8",
# "-ORBtraceLevel", "40"
# "-ORBtraceExceptions", "1",
# "-ORBtraceFile", "/tmp/debug-corba.log"]
orb = CORBA.ORB_init(["-ORBnativeCharCodeSet", "UTF-8"], CORBA.ORB_ID)

class Corba(object):
    def __init__(self, ior='localhost', context_name='fred', export_modules=None):
        object.__init__(self)
        self.ior = ior
        self.context_name = context_name
        self.context = None
        self.orb = orb

        # assign modules as attribute of this instance (i.e. corba.ccReg = sys.modules['ccReg'])
        if export_modules:
            for mod in export_modules:
                setattr(self, mod, sys.modules[mod])

    def connect(self):
        obj = orb.string_to_object('corbaname::' + self.ior)
        self.context = obj._narrow(CosNaming.NamingContext)

    def get_object(self, name, idl_type_str):
        if self.context is None:
            self.connect()
        cosname = [CosNaming.NameComponent(self.context_name, "context"),
                   CosNaming.NameComponent(name, "Object")]
        obj = self.context.resolve(cosname)

        # get idl type from idl_type_str:
        idl_type_parts = idl_type_str.split('.')
        idl_type = getattr(self, idl_type_parts[0]) # e.g. self.ccReg
        for part in idl_type_parts[1:]:
            idl_type = getattr(idl_type, part)

        return obj._narrow(idl_type)
