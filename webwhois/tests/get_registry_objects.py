from django.utils.decorators import method_decorator

from webwhois.utils import CCREG_MODULE, WHOIS_MODULE
from webwhois.utils.corba_wrapper import WebwhoisCorbaRecoder


def corba_wrapper(fnc):
    def wrap(*args, **kwargs):
        return recoder.decode(fnc(*args, **kwargs))
    return wrap

corba_wrapper_m = method_decorator(corba_wrapper)
recoder = WebwhoisCorbaRecoder("utf-8")


class GetRegistryObjectMixin(object):
    """
    Works together with CorbaInitMixin in webwhois.tests.utils.py and setUp:

    def setUp(self):
        self.CORBA = apply_patch...
    """

    CORBA = None

    def _get_contact_status(self):
        return [
            WHOIS_MODULE.ObjectStatusDesc(handle='serverDeleteProhibited', name='Deletion forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverTransferProhibited',
                                          name='Sponsoring registrar change forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverUpdateProhibited', name='Update forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverBlocked', name='Domain blocked'),
            WHOIS_MODULE.ObjectStatusDesc(handle='linked', name='Has relation to other records in the registry'),
            WHOIS_MODULE.ObjectStatusDesc(handle='deleteCandidate', name='To be deleted'),
            WHOIS_MODULE.ObjectStatusDesc(handle='conditionallyIdentifiedContact',
                                          name='Contact is conditionally identified'),
            WHOIS_MODULE.ObjectStatusDesc(handle='identifiedContact', name='Contact is identified'),
            WHOIS_MODULE.ObjectStatusDesc(handle='validatedContact', name='Contact is validated'),
            WHOIS_MODULE.ObjectStatusDesc(handle='mojeidContact', name='MojeID contact'),
            WHOIS_MODULE.ObjectStatusDesc(handle='contactInManualVerification',
                                          name='Contact is being verified by CZ.NIC customer support'),
            WHOIS_MODULE.ObjectStatusDesc(handle='contactPassedManualVerification',
                                          name='Contact has been verified by CZ.NIC customer support'),
            WHOIS_MODULE.ObjectStatusDesc(handle='contactFailedManualVerification',
                                          name='Contact has failed the verification by CZ.NIC customer support'),
        ]

    def _get_nsset_status(self):
        return [
            WHOIS_MODULE.ObjectStatusDesc(handle='serverDeleteProhibited', name='Deletion forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverTransferProhibited',
                                          name='Sponsoring registrar change forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverUpdateProhibited', name='Update forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='linked', name='Has relation to other records in the registry'),
            WHOIS_MODULE.ObjectStatusDesc(handle='deleteCandidate', name='To be deleted')
        ]

    def _get_keyset_status(self):
        return [
            WHOIS_MODULE.ObjectStatusDesc(handle='serverDeleteProhibited', name='Deletion forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverTransferProhibited',
                                          name='Sponsoring registrar change forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverUpdateProhibited', name='Update forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='linked', name='Has relation to other records in the registry'),
            WHOIS_MODULE.ObjectStatusDesc(handle='deleteCandidate', name='To be deleted')
        ]

    def _get_domain_status(self):
        return [
            WHOIS_MODULE.ObjectStatusDesc(handle='serverDeleteProhibited', name='Deletion forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverRenewProhibited', name='Registration renewal forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverTransferProhibited',
                                          name='Sponsoring registrar change forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverUpdateProhibited', name='Update forbidden'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverOutzoneManual',
                                          name='The domain is administratively kept out of zone'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverInzoneManual',
                                          name='The domain is administratively kept in zone'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverBlocked', name='Domain blocked'),
            WHOIS_MODULE.ObjectStatusDesc(handle='expired', name='Domain expired'),
            WHOIS_MODULE.ObjectStatusDesc(handle='notValidated', name='Domain not validated'),
            WHOIS_MODULE.ObjectStatusDesc(handle='outzone', name="The domain isn't generated in the zone"),
            WHOIS_MODULE.ObjectStatusDesc(handle='deleteCandidate', name='To be deleted'),
            WHOIS_MODULE.ObjectStatusDesc(handle='serverRegistrantChangeProhibited',
                                          name='Registrant change forbidden'),
        ]

    @corba_wrapper_m
    def _get_contact(self, **kwargs):
        disclose = kwargs.pop("disclose", True)
        address = WHOIS_MODULE.PlaceAddress(street1='Street 756/48', street2='', street3='', city='Prague',
                                            stateorprovince='', postalcode='12300', country_code='CZ')
        obj = WHOIS_MODULE.Contact(
            handle='KONTAKT',
            organization=WHOIS_MODULE.DisclosableString(value='Company L.t.d.', disclose=disclose),
            name=WHOIS_MODULE.DisclosableString(value='Arnold Rimmer', disclose=disclose),
            address=WHOIS_MODULE.DisclosablePlaceAddress(value=address, disclose=disclose),
            phone=WHOIS_MODULE.DisclosableString(value='+420.728012345', disclose=disclose),
            fax=WHOIS_MODULE.DisclosableString(value='+420.728023456', disclose=disclose),
            email=WHOIS_MODULE.DisclosableString(value='rimmer@foo.foo', disclose=disclose),
            notify_email=WHOIS_MODULE.DisclosableString(value='notify-rimmer@foo.foo', disclose=disclose),
            vat_number=WHOIS_MODULE.DisclosableString(value='CZ456123789', disclose=disclose),
            identification=WHOIS_MODULE.DisclosableContactIdentification(
                value=WHOIS_MODULE.ContactIdentification(identification_type='OP', identification_data='333777000'),
                disclose=disclose,
            ),
            creating_registrar_handle='REG-FRED_A',
            sponsoring_registrar_handle='REG-FRED_A',
            created=CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(day=15, month=12, year=2015),
                                              hour=7, minute=56, second=24),
            changed=CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(day=16, month=12, year=2015),
                                              hour=8, minute=32, second=12),
            last_transfer=CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(day=17, month=12, year=2015),
                                                    hour=9, minute=48, second=25),
            statuses=['linked']
        )
        field_names = obj.__dict__.keys()
        for key, value in kwargs.items():
            assert key in field_names, "Unknown arg '%s' in _get_contact." % key
            setattr(obj, key, value)
        return obj

    def _get_place_address(self, **kwargs):
        obj = WHOIS_MODULE.PlaceAddress(street1='The street 123', street2='', street3='', city='Prague',
                                        stateorprovince='', postalcode='13200', country_code='CZ')
        field_names = obj.__dict__.keys()
        for key, value in kwargs.items():
            assert key in field_names, "Unknown arg '%s' in _get_place_address." % key
            setattr(obj, key, value)
        return obj

    def _get_registrar(self, **kwargs):
        address = WHOIS_MODULE.PlaceAddress(street1='The street 123', street2='', street3='', city='Prague',
                                            stateorprovince='', postalcode='12300', country_code='CZ')
        obj = WHOIS_MODULE.Registrar(
            handle='REG-FRED_A', name="Company A L.t.d.", organization='Testing registrar A', url='www.nic.cz',
            phone='+420.72645123', fax='+420.72645124', address=address,
        )
        field_names = obj.__dict__.keys()
        for key, value in kwargs.items():
            assert key in field_names, "Unknown arg '%s' in _get_registrar." % key
            setattr(obj, key, value)
        return obj

    @corba_wrapper_m
    def _get_nsset(self, **kwargs):
        fqdn1 = kwargs.pop('fqdn1', 'a.ns.nic.cz')
        fqdn2 = kwargs.pop('fqdn2', 'b.ns.nic.cz')
        ip1 = WHOIS_MODULE.IPAddress(address='194.0.12.1', version=WHOIS_MODULE.IPv4)
        ip2 = WHOIS_MODULE.IPAddress(address='194.0.13.1', version=WHOIS_MODULE.IPv4)
        obj = WHOIS_MODULE.NSSet(
            handle='NSSET-1',
            nservers=[
                WHOIS_MODULE.NameServer(fqdn=fqdn1, ip_addresses=[ip1]),
                WHOIS_MODULE.NameServer(fqdn=fqdn2, ip_addresses=[ip2]),
            ],
            tech_contact_handles=['KONTAKT'],
            registrar_handle='REG-FRED_A',
            created=CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(day=9, month=12, year=2015),
                                              hour=16, minute=16, second=30),
            changed=CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(day=10, month=12, year=2015),
                                              hour=17, minute=17, second=31),
            last_transfer=CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(day=11, month=12, year=2015),
                                                    hour=18, minute=18, second=32),
            statuses=['linked']
        )
        field_names = obj.__dict__.keys()
        for key, value in kwargs.items():
            assert key in field_names, "Unknown arg '%s' in _get_nsset." % key
            setattr(obj, key, value)
        return obj

    @corba_wrapper_m
    def _get_keyset(self, **kwargs):
        obj = WHOIS_MODULE.KeySet(
            handle='KEYSID-1',
            dns_keys=[
                WHOIS_MODULE.DNSKey(flags=257, protocol=3, alg=5,
                                    public_key='AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxWEA4RJ9Ao6LCWheg8')
            ],
            tech_contact_handles=['KONTAKT'],
            registrar_handle='REG-FRED_A',
            created=CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(day=9, month=12, year=2015),
                                              hour=16, minute=16, second=30),
            changed=CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(day=10, month=12, year=2015),
                                              hour=17, minute=17, second=31),
            last_transfer=CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(day=11, month=12, year=2015),
                                                    hour=18, minute=18, second=32),
            statuses=['linked']
        )
        field_names = obj.__dict__.keys()
        for key, value in kwargs.items():
            assert key in field_names, "Unknown arg '%s' in _get_keyset." % key
            setattr(obj, key, value)
        return obj

    @corba_wrapper_m
    def _get_domain(self, **kwargs):
        obj = WHOIS_MODULE.Domain(
            handle='fred.cz',
            registrant_handle='KONTAKT',
            admin_contact_handles=['KONTAKT'],
            nsset_handle='NSSET-1',
            keyset_handle='KEYSID-1',
            registrar_handle='REG-FRED_A',
            statuses=['serverDeleteProhibited', 'serverUpdateProhibited'],
            registered=CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(day=9, month=12, year=2015),
                                                 hour=16, minute=16, second=30),
            changed=CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(day=10, month=12, year=2015),
                                              hour=17, minute=17, second=31),
            last_transfer=CCREG_MODULE.DateTimeType(date=CCREG_MODULE.DateType(day=11, month=12, year=2015),
                                                    hour=18, minute=18, second=32),
            expire=CCREG_MODULE.DateType(day=9, month=12, year=2018),
            expire_time_estimate=CCREG_MODULE.DateType(day=9, month=12, year=2018),
            expire_time_actual=None,
            validated_to=None,
            validated_to_time_estimate=None,
            validated_to_time_actual=None
        )
        field_names = obj.__dict__.keys()
        for key, value in kwargs.items():
            assert key in field_names, "Unknown arg '%s' in _get_domain." % key
            setattr(obj, key, value)
        return obj

    def _get_registrar_groups(self):
        return [
            WHOIS_MODULE.RegistrarGroup(name='certified', members=['REG-FRED_A', 'REG-FRED_B', 'REG-MOJEID']),
            WHOIS_MODULE.RegistrarGroup(name='dnssec', members=['REG-FRED_A']),
            WHOIS_MODULE.RegistrarGroup(name='ipv6', members=['REG-FRED_B']),
            WHOIS_MODULE.RegistrarGroup(name='mojeid', members=['REG-FRED_A']),
            WHOIS_MODULE.RegistrarGroup(name='uncertified', members=['REG-FRED_C'])
        ]

    def _get_registrar_certs(self):
        return [
            WHOIS_MODULE.RegistrarCertification(registrar_handle='REG-FRED_A', score=2, evaluation_file_id=1L),
            WHOIS_MODULE.RegistrarCertification(registrar_handle='REG-MOJEID', score=8, evaluation_file_id=2L),
        ]

    def _get_registrars(self):
        return [
            WHOIS_MODULE.Registrar(handle='REG-FRED_A', name="Company A L.t.d.", organization='Testing registrar A',
                                   url='www.fred-a.cz', phone='', fax='', address=self._get_place_address()),
            WHOIS_MODULE.Registrar(handle='REG-FRED_B', name="Company B L.t.d.", organization='Testing registrar B',
                                   url='http://www.fred-b.cz', phone='', fax='', address=self._get_place_address()),
            WHOIS_MODULE.Registrar(handle='REG-FRED_C', name="Company C L.t.d.",
                                   organization='Testing registrar NOCRED', url='https://www.no-credit.cz',
                                   phone='', fax='', address=self._get_place_address()),
            WHOIS_MODULE.Registrar(handle='REG-MOJEID', name="MojeID s.r.o.", organization='MojeID registrar',
                                   url='www.mojeid.cz', phone='', fax='', address=self._get_place_address()),
        ]
