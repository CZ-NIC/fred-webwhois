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

"""Webwhois views.

isort:skip_file
"""
from .detail_contact import ContactDetailMixin, ContactDetailView
from .detail_keyset import KeysetDetailMixin, KeysetDetailView
from .detail_nsset import NssetDetailMixin, NssetDetailView
from .detail_domain import DomainDetailMixin, DomainDetailView
from .form_whois import WhoisFormView
from .public_request import BlockObjectFormView, CustomEmailView, EmailInRegistryView, NotarizedLetterView, \
    PersonalInfoFormView, PublicResponseNotFoundView, SendPasswordFormView, ServeNotarizedLetterView, \
    UnblockObjectFormView
from .record_statement import ServeRecordStatementView
from .registrar import DownloadEvalFileView, RegistrarDetailMixin, RegistrarDetailView, RegistrarListMixin, \
    RegistrarListView
from .resolve_handle_type import ResolveHandleTypeMixin, ResolveHandleTypeView

__all__ = ['BlockObjectFormView', 'ContactDetailMixin', 'ContactDetailView', 'CustomEmailView', 'DomainDetailMixin',
           'DomainDetailView', 'DownloadEvalFileView', 'EmailInRegistryView', 'KeysetDetailMixin', 'KeysetDetailView',
           'NotarizedLetterView', 'NssetDetailMixin', 'NssetDetailView', 'PersonalInfoFormView',
           'PublicResponseNotFoundView', 'RegistrarDetailMixin', 'RegistrarDetailView', 'RegistrarListMixin',
           'RegistrarListView', 'ResolveHandleTypeMixin', 'ResolveHandleTypeView', 'SendPasswordFormView',
           'ServeNotarizedLetterView', 'ServeRecordStatementView', 'UnblockObjectFormView', 'WhoisFormView']
