#
# Copyright (C) 2019-2021  CZ.NIC, z. s. p. o.
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

"""Custom views for tests."""
from typing import Any, Dict

from django.views.generic import TemplateView

from webwhois.views import (ContactDetailView, DomainDetailView, KeysetDetailView, NssetDetailView, RegistrarDetailView,
                            RegistrarListView, ResolveHandleTypeView)
from webwhois.views.base import RegistryObjectMixin


class CustomRegistrarListView(RegistrarListView):
    """RegistrarListView with overridden _registrar_row."""

    def _registrar_row(self, data):
        """Override the method to test deprecation warning."""
        data['custom'] = True
        return super(RegistrarListView, self)._registrar_row(data)


class GetObjectRegistryView(RegistryObjectMixin, TemplateView):
    """View based on RegistryObjectMixin with custom get_object."""

    object_type_name = 'object'
    template_name = 'webwhois/block_main.html'

    def _get_object(self, handle: str) -> Any:
        return {
            'handle': handle,
            'method': 'get_object',
        }


class LoadObjectRegistryView(GetObjectRegistryView):
    """View based on RegistryObjectMixin with custom load_registry_object."""

    @classmethod
    def load_registry_object(cls, context: Dict, handle: str) -> Any:
        context[cls._registry_objects_key][cls.object_type_name] = {
            'detail': {'handle': handle, 'method': 'load_registry_object'},
        }


class LoadRegistryObjectMixin:
    @classmethod
    def load_registry_object(cls, context, handle):
        super().load_registry_object(context, handle)  # type: ignore[misc]


class LoadContactDetailView(LoadRegistryObjectMixin, ContactDetailView):
    """ContactDetailView with custom load_registry_object."""


class LoadDomainDetailView(LoadRegistryObjectMixin, DomainDetailView):
    """DomainDetailView with custom load_registry_object."""


class LoadKeysetDetailView(LoadRegistryObjectMixin, KeysetDetailView):
    """KeysetDetailView with custom load_registry_object."""


class LoadNssetDetailView(LoadRegistryObjectMixin, NssetDetailView):
    """NssetDetailView with custom load_registry_object."""


class LoadRegistrarDetailView(LoadRegistryObjectMixin, RegistrarDetailView):
    """RegistrarDetailView with custom load_registry_object."""


class LoadResolveHandleTypeView(LoadRegistryObjectMixin, ResolveHandleTypeView):
    """ResolveHandleTypeView with custom load_registry_object."""
