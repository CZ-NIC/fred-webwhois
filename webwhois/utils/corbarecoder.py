import types
import sys
import datetime

from pyfco.corbarecoder import CorbaRecoder


class WebwhoisCorbaRecoder(CorbaRecoder):

    def _decode_instance(self, answer):
        ccReg = sys.modules['ccReg']
        if isinstance(answer, ccReg.DateTimeType):
            corba_date = answer.date
            return datetime.datetime(corba_date.year, corba_date.month, corba_date.day,
                                     answer.hour, answer.minute, answer.second)
        elif isinstance(answer, ccReg.DateType):
            return datetime.date(answer.year, answer.month, answer.day)
        else:
            return super(WebwhoisCorbaRecoder, self)._decode_instance(answer)


recoder = WebwhoisCorbaRecoder("utf-8")
c2u = recoder.decode  # recode from corba string to unicode
u2c = recoder.encode  # recode from unicode to strings
