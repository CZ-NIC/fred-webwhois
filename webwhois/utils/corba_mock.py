import sys
from django.conf import settings
from omniORB import importIDL


importIDL('%s/%s' % (settings.CORBA_IDL_ROOT_PATH, settings.CORBA_IDL_FILEMANAGER_FILENAME))
importIDL('%s/%s' % (settings.CORBA_IDL_ROOT_PATH, settings.CORBA_IDL_WHOIS_FILENAME))
Registry = sys.modules['Registry']
ccReg = sys.modules['ccReg']

class WhoisIntfMock(object):

    def get_registrars(self):
        return [Registry.Whois.Registrar(
                    handle='REG-FRED_A',
                    organization='Testing registrar A',
                    url='www.nic.cz',
                    phone='123456',
                    fax='58741',
                    address=Registry.Whois.PlaceAddress(
                        street1='',
                        street2='',
                        street3='',
                        city='',
                        stateorprovince='',
                        postalcode='', country_code='CZ')
                ),
                Registry.Whois.Registrar(
                    handle='REG-FRED_B',
                    organization='Testing registrar B',
                    url='www.cin.cz',
                    phone='654987',
                    fax='64651',
                    address=Registry.Whois.PlaceAddress(
                        street1='Str1',
                        street2='Str2',
                        street3='',
                        city='City 1',
                        stateorprovince='State',
                        postalcode='15015', country_code='EN')
                ),
                Registry.Whois.Registrar(
                    handle='REG-FRED_C',
                    organization='Testing registrar C',
                    url='www.ccc.cc',
                    phone='654987',
                    fax='64651',
                    address=Registry.Whois.PlaceAddress(
                        street1='Str1',
                        street2='Str2',
                        street3='',
                        city='City 1',
                        stateorprovince='State',
                        postalcode='15015', country_code='RU')
                ),
                ]

    def get_domain_by_handle(self, handle):
        if handle.lower() == u'fred.cz':
            return Registry.Whois.Domain(
              handle='fred.cz',
              registrant_handle='KONTAKT',
              admin_contact_handles=['KONTAKT'],
              nsset_handle='NSSET-1',
              keyset_handle='KEYSID-1',
              registrar_handle='REG-FRED_A',
              statuses=['ok', 'serverRenewProhibited', 'test'],
              registered=ccReg.DateTimeType(date=ccReg.DateType(day=2, month=6, year=2015), hour=7, minute=29, second=57),
              changed=None,
              last_transfer=None,
              expire=ccReg.DateType(day=2, month=6, year=2018),
              validated_to=None)
        elif handle.lower() == u'invalid':
            raise Registry.Whois.INVALID_LABEL
        elif handle.lower() == u'nic.cz':
            raise Registry.Whois.INTERNAL_SERVER_ERROR
        elif handle.lower() == u'many.labels.cz':
            raise Registry.Whois.TOO_MANY_LABELS
        elif handle.lower() == u'unmanaged.zone':
            raise Registry.Whois.UNMANAGED_ZONE
        else:
            raise Registry.Whois.OBJECT_NOT_FOUND

    def get_nsset_by_handle(self, handle):
        if handle.upper() == u'NSSET-1':
            return Registry.Whois.NSSet(
                handle='NSSET-1',
                nservers=[
                    Registry.Whois.NameServer(fqdn='a.ns.nic.cz',
                                              ip_addresses=[Registry.Whois.IPAddress(address='194.0.12.1', version=Registry.Whois.IPv4)]),
                    Registry.Whois.NameServer(fqdn='b.ns.nic.cz',
                                              ip_addresses=[Registry.Whois.IPAddress(address='194.0.13.1', version=Registry.Whois.IPv4)])],
                tech_contact_handles=['KONTAKT'],
                registrar_handle='REG-FRED_A',
                created=ccReg.DateTimeType(date=ccReg.DateType(day=2, month=6, year=2015), hour=7, minute=29, second=56),
                changed=None,
                last_transfer=None,
                statuses=['serverUpdateProhibited'])
        elif handle.upper() == u'INVALID':
            raise Registry.Whois.INVALID_HANDLE
        elif handle.upper() == u'NSSET-0':
            raise Registry.Whois.INTERNAL_SERVER_ERROR
        else:
            raise Registry.Whois.OBJECT_NOT_FOUND

    def get_keyset_by_handle(self, handle):
        if handle.upper() == u'KEYSID-1':
            return Registry.Whois.KeySet(
                handle='KEYSID-1',
                dns_keys=[Registry.Whois.DNSKey(flags=257,
                                                protocol=3,
                                                alg=5,
                                                public_key='AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxWEA4RJ9Ao6LCWheg8')],
                tech_contact_handles=['KONTAKT'],
                registrar_handle='REG-FRED_A',
                created=ccReg.DateTimeType(date=ccReg.DateType(day=2, month=6, year=2015), hour=7, minute=29, second=57),
                changed=None,
                last_transfer=None,
                statuses=['serverInzoneManual'])
        elif handle.upper() == u'INVALID':
            raise Registry.Whois.INVALID_HANDLE
        elif handle.upper() == u'KEYSID-0':
            raise Registry.Whois.INTERNAL_SERVER_ERROR
        else:
            raise Registry.Whois.OBJECT_NOT_FOUND

    def get_registrar_by_handle(self, handle):
        if handle.upper() in (u'REG-FRED_A', u'REG-FRED_B', u'REG-FRED_C'):
            return Registry.Whois.Registrar(
                handle=handle.upper(),
                organization='Testing registrar %s' % handle.upper(),
                url='www.nic.cz',
                phone='123456',
                fax='58741',
                address=Registry.Whois.PlaceAddress(
                    street1='',
                    street2='',
                    street3='',
                    city='',
                    stateorprovince='',
                    postalcode='', country_code='CZ'))
        elif handle.upper() == u'REG-INVALID':
            raise Registry.Whois.INVALID_HANDLE
        elif handle.upper() == u'REG-0':
            raise Registry.Whois.INTERNAL_SERVER_ERROR
        else:
            raise Registry.Whois.OBJECT_NOT_FOUND

    def get_contact_by_handle(self, handle):
        if handle.upper() == u'KONTAKT':
            return Registry.Whois.Contact(
                handle='KONTAKT',
                organization=Registry.Whois.DisclosableString(value='Firma s.r.o.', disclose=True),
                name=Registry.Whois.DisclosableString(value='Jan Novak', disclose=True),
                address=Registry.Whois.DisclosablePlaceAddress(
                    value=Registry.Whois.PlaceAddress(
                        street1='Namesti republiky 1230/12',
                        street2='',
                        street3='',
                        city='Praha',
                        stateorprovince='',
                        postalcode='12000',
                        country_code='CZ'),
                    disclose=True),
                phone=Registry.Whois.DisclosableString(value=None, disclose=True),
                fax=Registry.Whois.DisclosableString(value='+420.222745111', disclose=True),
                email=Registry.Whois.DisclosableString(value='info@mymail.cz', disclose=True),
                notify_email=Registry.Whois.DisclosableString(value=None, disclose=False),
                vat_number=Registry.Whois.DisclosableString(value=None, disclose=True),
                identification=Registry.Whois.DisclosableContactIdentification(
                    value=Registry.Whois.ContactIdentification(identification_type='OP', identification_data='99999'),
                    disclose=True),
                creating_registrar_handle='REG-FRED_A',
                sponsoring_registrar_handle='REG-FRED_A',
                created=ccReg.DateTimeType(date=ccReg.DateType(day=2, month=6, year=2015), hour=7, minute=29, second=55),
                changed=None,
                last_transfer=None,
                statuses=['linked', 'conditionallyIdentifiedContact', 'contactFailedManualVerification'])
        elif handle.upper() == u'KEYSID-1':
            return Registry.Whois.Contact(
                handle='KEYSID-1',
                organization=Registry.Whois.DisclosableString(value='Duplicita s Keyset', disclose=True),
                name=Registry.Whois.DisclosableString(value='Duplicita', disclose=True),
                address=Registry.Whois.DisclosablePlaceAddress(
                    value=Registry.Whois.PlaceAddress(
                        street1='Namesti republiky 1230/12',
                        street2='',
                        street3='',
                        city='Praha',
                        stateorprovince='',
                        postalcode='12000',
                        country_code='CZ'),
                    disclose=True),
                phone=Registry.Whois.DisclosableString(value=None, disclose=True),
                fax=Registry.Whois.DisclosableString(value='+420.222745111', disclose=True),
                email=Registry.Whois.DisclosableString(value='info@mymail.cz', disclose=True),
                notify_email=Registry.Whois.DisclosableString(value=None, disclose=False),
                vat_number=Registry.Whois.DisclosableString(value=None, disclose=True),
                identification=Registry.Whois.DisclosableContactIdentification(
                    value=Registry.Whois.ContactIdentification(identification_type='XX', identification_data='132456'),
                    disclose=True),
                creating_registrar_handle='REG-FRED_A',
                sponsoring_registrar_handle='REG-FRED_A',
                created=ccReg.DateTimeType(date=ccReg.DateType(day=2, month=6, year=2015), hour=7, minute=29, second=55),
                changed=None,
                last_transfer=None,
                statuses=['ok', 'serverRegistrantChangeProhibited'])
        elif handle.upper() == u'INVALID':
            raise Registry.Whois.INVALID_HANDLE
        elif handle.upper() == u'NIC':
            raise Registry.Whois.INTERNAL_SERVER_ERROR
        else:
            raise Registry.Whois.OBJECT_NOT_FOUND


    def _get_desc(self, lang):
        if lang == 'de':
            raise Registry.Whois.MISSING_LOCALIZATION
        return [Registry.Whois.ObjectStatusDesc(handle='ok', name='Objekt je bez omezen\xc3\xad'),
                Registry.Whois.ObjectStatusDesc(handle='serverDeleteProhibited', name='Nen\xc3\xad povoleno smaz\xc3\xa1n\xc3\xad'),
                Registry.Whois.ObjectStatusDesc(handle='serverRenewProhibited', name='Nen\xc3\xad povoleno prodlou\xc5\xbeen\xc3\xad registrace objektu'),
                Registry.Whois.ObjectStatusDesc(handle='serverTransferProhibited', name='Nen\xc3\xad povolena zm\xc4\x9bna ur\xc4\x8den\xc3\xa9ho registr\xc3\xa1tora'),
                Registry.Whois.ObjectStatusDesc(handle='serverUpdateProhibited', name='Nen\xc3\xad povolena zm\xc4\x9bna \xc3\xbadaj\xc5\xaf'),
                Registry.Whois.ObjectStatusDesc(handle='contactFailedManualVerification', name='Dom\xc3\xa9na je administrativn\xc4\x9b vy\xc5\x99azena ze z\xc3\xb3ny'),
                Registry.Whois.ObjectStatusDesc(handle='serverInzoneManual', name='Dom\xc3\xa9na je administrativn\xc4\x9b za\xc5\x99azena do z\xc3\xb3ny'),
                Registry.Whois.ObjectStatusDesc(handle='conditionallyIdentifiedContact', name='Dom\xc3\xa9na je blokov\xc3\xa1na'),
                Registry.Whois.ObjectStatusDesc(handle='expired', name='Dom\xc3\xa9na je po expiraci'),
                Registry.Whois.ObjectStatusDesc(handle='notValidated', name='Dom\xc3\xa9na nen\xc3\xad validov\xc3\xa1na'),
                Registry.Whois.ObjectStatusDesc(handle='linked', name='Dom\xc3\xa9na nen\xc3\xad generov\xc3\xa1na do z\xc3\xb3ny'),
                Registry.Whois.ObjectStatusDesc(handle='deleteCandidate', name='Ur\xc4\x8deno ke zru\xc5\xa1en\xc3\xad'),
                Registry.Whois.ObjectStatusDesc(handle='serverRegistrantChangeProhibited', name='Nen\xc3\xad povolena zm\xc4\x9bna dr\xc5\xbeitele'),
                ]

    def get_domain_status_descriptions(self, lang):
        return self._get_desc(lang)
    def get_contact_status_descriptions(self, lang):
        return self._get_desc(lang)
    def get_nsset_status_descriptions(self, lang):
        return self._get_desc(lang)
    def get_keyset_status_descriptions(self, lang):
        return self._get_desc(lang)

    def get_registrar_groups(self):
        return [Registry.Whois.RegistrarGroup(name='certified', members=['REG-FRED_A', 'REG-FRED_B']),
                Registry.Whois.RegistrarGroup(name='dnssec', members=['REG-FRED_A']),
                Registry.Whois.RegistrarGroup(name='ipv6', members=['REG-FRED_B', 'REG-FRED_C']),
                Registry.Whois.RegistrarGroup(name='mojeid', members=['REG-FRED_A']),
                Registry.Whois.RegistrarGroup(name='testgroup1', members=['REG-FRED_A', 'REG-FRED_B']),
                Registry.Whois.RegistrarGroup(name='uncertified', members=['REG-FRED_C']),
                ]

    def get_registrar_certification_list(self):
        return [Registry.Whois.RegistrarCertification(registrar_handle='REG-FRED_B', score=3, evaluation_file_id=1L),
                Registry.Whois.RegistrarCertification(registrar_handle='REG-FRED_C', score=1, evaluation_file_id=4L),
                ]


class FileManagerMock(object):

    class FileDownloadMock(object):

        def __init__(self, file_id):
            self.file_id = file_id

        def download(self, bytes):
            if self.file_id == 1:
                return 'test\n'[0:bytes]
            elif self.file_id == 4:
                return '<statement>\n    <account_number>617</account_number>\n</statement>\n'[0:bytes]

        def finalize_download(self):
            pass

    def info(self, file_id):
        if file_id == 1:
            return ccReg.FileInfo(id=1, name='test.txt', path='2015/6/2/1', mimetype='text/plain',
                                  filetype=6, crdate='2015-06-02 07:29:54.079036', size=5L)
        elif file_id == 4:
            return ccReg.FileInfo(id=4, name='example.xml', path='2015/6/2/2', mimetype='text/xml',
                                  filetype=4, crdate='2015-06-02 07:29:54.506256', size=66L)
        elif file_id == 0:
            raise ccReg.FileManager.InternalError
        else:
            raise ccReg.FileManager.IdNotFound

    def load(self, file_id):
        if file_id in (1, 4):
            return FileManagerMock.FileDownloadMock(file_id)
        elif file_id == 0:
            raise ccReg.FileManager.InternalError
        elif file_id == 2:
            raise ccReg.FileManager.FileNotFound
        else:
            raise ccReg.FileManager.IdNotFound
