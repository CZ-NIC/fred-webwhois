#
# Copyright (C) 2015-2020  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.
from django.utils.decorators import method_decorator
from fred_idl.Registry import IsoDate, IsoDateTime
from fred_idl.Registry.Whois import Contact, ContactIdentification, DisclosableContactIdentification, \
    DisclosablePlaceAddress, DisclosableString, DNSKey, Domain, IPAddress, IPv4, KeySet, NameServer, NSSet, \
    ObjectStatusDesc, PlaceAddress, Registrar, RegistrarCertification

from webwhois.constants import STATUS_CONDITIONALLY_IDENTIFIED, STATUS_DELETE_CANDIDATE, STATUS_IDENTIFIED, \
    STATUS_LINKED, STATUS_VALIDATED, STATUS_VERIFICATION_FAILED, STATUS_VERIFICATION_IN_PROCESS, \
    STATUS_VERIFICATION_PASSED
from webwhois.utils.corba_wrapper import WebwhoisCorbaRecoder


def corba_wrapper(fnc):
    def wrap(*args, **kwargs):
        return recoder.decode(fnc(*args, **kwargs))
    return wrap


corba_wrapper_m = method_decorator(corba_wrapper)
recoder = WebwhoisCorbaRecoder("utf-8")


class GetRegistryObjectMixin(object):
    """Utilities for Corba struct creations."""

    def _get_contact_status(self):
        return [
            ObjectStatusDesc(handle=STATUS_LINKED, name='Has relation to other records in the registry'),
            ObjectStatusDesc(handle=STATUS_DELETE_CANDIDATE, name='To be deleted'),
            ObjectStatusDesc(handle=STATUS_CONDITIONALLY_IDENTIFIED, name='Contact is conditionally identified'),
            ObjectStatusDesc(handle=STATUS_IDENTIFIED, name='Contact is identified'),
            ObjectStatusDesc(handle=STATUS_VALIDATED, name='Contact is validated'),
            ObjectStatusDesc(handle=STATUS_VERIFICATION_IN_PROCESS,
                             name='Contact is being verified by CZ.NIC customer support'),
            ObjectStatusDesc(handle=STATUS_VERIFICATION_PASSED,
                             name='Contact has been verified by CZ.NIC customer support'),
            ObjectStatusDesc(handle=STATUS_VERIFICATION_FAILED,
                             name='Contact has failed the verification by CZ.NIC customer support'),
            # This is sort of deprecation.
            ObjectStatusDesc(handle='mojeidContact', name='MojeID contact'),
        ]

    def _get_nsset_status(self):
        return [
            ObjectStatusDesc(handle=STATUS_LINKED, name='Has relation to other records in the registry'),
            ObjectStatusDesc(handle=STATUS_DELETE_CANDIDATE, name='To be deleted')
        ]

    def _get_keyset_status(self):
        return [
            ObjectStatusDesc(handle=STATUS_LINKED, name='Has relation to other records in the registry'),
            ObjectStatusDesc(handle=STATUS_DELETE_CANDIDATE, name='To be deleted')
        ]

    def _get_domain_status(self):
        return [
            ObjectStatusDesc(handle=STATUS_DELETE_CANDIDATE, name='To be deleted'),
        ]

    @corba_wrapper_m
    def _get_contact(self, **kwargs):
        disclose = kwargs.pop("disclose", True)
        address = PlaceAddress(
            street1='Street 756/48', street2='', street3='', city='Prague', stateorprovince='', postalcode='12300',
            country_code='CZ')
        obj = Contact(
            handle='KONTAKT',
            organization=DisclosableString(value='Company L.t.d.', disclose=disclose),
            name=DisclosableString(value='Arnold Rimmer', disclose=disclose),
            address=DisclosablePlaceAddress(value=address, disclose=disclose),
            phone=DisclosableString(value='+420.728012345', disclose=disclose),
            fax=DisclosableString(value='+420.728023456', disclose=disclose),
            email=DisclosableString(value='rimmer@foo.foo', disclose=disclose),
            notify_email=DisclosableString(value='notify-rimmer@foo.foo', disclose=disclose),
            vat_number=DisclosableString(value='CZ456123789', disclose=disclose),
            identification=DisclosableContactIdentification(
                value=ContactIdentification(identification_type='OP', identification_data='333777000'),
                disclose=disclose,
            ),
            creating_registrar_handle='REG-FRED_A',
            sponsoring_registrar_handle='REG-FRED_A',
            created=IsoDateTime('2015-12-15T07:56:24Z'),
            changed=IsoDateTime('2015-12-16T08:32:12Z'),
            last_transfer=IsoDateTime('2015-12-17T09:48:25Z'),
            statuses=[STATUS_LINKED]
        )
        field_names = obj.__dict__.keys()
        for key, value in kwargs.items():
            assert key in field_names, "Unknown arg '%s' in _get_contact." % key
            setattr(obj, key, value)
        return obj

    def _get_registrar(self):
        address = PlaceAddress(
            street1='The street 123', street2='', street3='', city='Prague', stateorprovince='', postalcode='12300',
            country_code='CZ')
        return Registrar(
            handle='REG-FRED_A', name="Company A L.t.d.", organization='Testing registrar A', url='www.nic.cz',
            phone='+420.72645123', fax='+420.72645124', address=address,
        )

    @corba_wrapper_m
    def _get_nsset(self, fqdn1='a.ns.nic.cz', fqdn2='b.ns.nic.cz'):
        ip1 = IPAddress(address='194.0.12.1', version=IPv4)
        ip2 = IPAddress(address='194.0.13.1', version=IPv4)
        return NSSet(
            handle='NSSET-1',
            nservers=[
                NameServer(fqdn=fqdn1, ip_addresses=[ip1]),
                NameServer(fqdn=fqdn2, ip_addresses=[ip2]),
            ],
            tech_contact_handles=['KONTAKT'],
            registrar_handle='REG-FRED_A',
            created=IsoDateTime('2015-12-09T16:16:30Z'),
            changed=IsoDateTime('2015-12-10T17:17:31Z'),
            last_transfer=IsoDateTime('2015-12-11T18:18:32Z'),
            statuses=[STATUS_LINKED]
        )

    @corba_wrapper_m
    def _get_keyset(self):
        return KeySet(
            handle='KEYSID-1',
            dns_keys=[
                DNSKey(flags=257, protocol=3, alg=5,
                       public_key='AwEAAddt2AkLfYGKgiEZB5SmIF8EvrjxNMH6HtxWEA4RJ9Ao6LCWheg8')
            ],
            tech_contact_handles=['KONTAKT'],
            registrar_handle='REG-FRED_A',
            created=IsoDateTime('2015-12-09T16:16:30Z'),
            changed=IsoDateTime('2015-12-10T17:17:31Z'),
            last_transfer=IsoDateTime('2015-12-11T18:18:32Z'),
            statuses=[STATUS_LINKED]
        )

    @corba_wrapper_m
    def _get_domain(self, **kwargs):
        obj = Domain(
            handle='fred.cz',
            registrant_handle='KONTAKT',
            admin_contact_handles=['KONTAKT'],
            nsset_handle='NSSET-1',
            keyset_handle='KEYSID-1',
            registrar_handle='REG-FRED_A',
            statuses=[],
            registered=IsoDateTime('2015-12-09T16:16:30Z'),
            changed=IsoDateTime('2015-12-10T17:17:31Z'),
            last_transfer=IsoDateTime('2015-12-11T18:18:32Z'),
            expire=IsoDate('2018-12-09'),
            expire_time_estimate=IsoDate('2018-12-09'),
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

    def _get_registrar_certs(self):
        return [
            RegistrarCertification(registrar_handle='REG-FRED_A', score=2, evaluation_file_id=1),
            RegistrarCertification(registrar_handle='REG-MOJEID', score=8, evaluation_file_id=2),
        ]
