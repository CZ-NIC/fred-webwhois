#
# Copyright (C) 2015-2022  CZ.NIC, z. s. p. o.
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
import random
import warnings
from typing import Iterable, Optional, cast

from django.http import Http404, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, View
from fred_idl.Registry.Whois import INVALID_HANDLE, OBJECT_NOT_FOUND

from webwhois.utils import FILE_MANAGER, WHOIS
from webwhois.views.base import BaseContextMixin, RegistryObjectMixin

from ..exceptions import WebwhoisError
from ..utils.deprecation import deprecated_context


class RegistrarDetailMixin(RegistryObjectMixin):
    """Detail of Registrar."""

    template_name = "webwhois/registrar.html"
    object_type_name = "registrar"

    @classmethod
    def load_registry_object(cls, context, handle):
        """Load registrar of the handle and append it into the context."""
        try:
            context[cls._registry_objects_key]["registrar"] = {
                "detail": WHOIS.get_registrar_by_handle(handle),
                "label": _("Registrar"),
            }
        except OBJECT_NOT_FOUND as error:
            raise WebwhoisError(
                'OBJECT_NOT_FOUND',
                title=_("Registrar not found"),
                message=cls.message_with_handle_in_html(_("No registrar matches %s handle."), handle),
            ) from error
        except INVALID_HANDLE as error:
            raise WebwhoisError(**cls.message_invalid_handle(handle)) from error


class RegistrarDetailView(RegistrarDetailMixin, TemplateView):
    """View with details of a registrar."""


class RegistrarListMixin(BaseContextMixin):
    """Mixin for a list of registrars.

    @cvar group_name: Name of the registrar group to filter results.
    """

    template_name = "webwhois/registrar_list.html"
    group_name: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super(RegistrarListMixin, self).__init__(*args, **kwargs)
        # Caches for backend responses
        self._groups = None
        self._certifications = None

    def get_registrars(self):
        """Return a list of registrars to be displayed.

        Results are filtered according to `group_name` attribute.
        """
        registrars = WHOIS.get_registrars()
        if self.group_name:
            groups = self.get_groups()
            if self.group_name not in groups:
                raise Http404('Registrar group {} not found.'.format(self.group_name))
            members = groups[self.group_name].members  # type: Iterable[str]
            registrars = [r for r in registrars if r.handle in members]
        return registrars

    def get_groups(self):
        """Return dictionary of registrar groups."""
        if self._groups is None:
            self._groups = {group.name: group for group in WHOIS.get_registrar_groups()}
        return self._groups

    def get_certifications(self):
        """Return dictionary of registrar certifications."""
        if self._certifications is None:
            self._certifications = {cert.registrar_handle: cert for cert in WHOIS.get_registrar_certification_list()}
        return self._certifications

    def get_registrar_context(self, registrar):
        """Return context for a registrar."""
        certification = self.get_certifications().get(registrar.handle)
        score = certification.score if certification else 0
        context = {"registrar": registrar, "cert": certification, "score": score, "stars": range(score)}
        if not getattr(self._registrar_row, 'prevent_warning', False):
            warn_msg = ("Method 'RegistrarListView._registrar_row' is deprecated in favor of "
                        "'RegistrarListView.get_registrar_context'.")
            warnings.warn(warn_msg, DeprecationWarning)
        return self._registrar_row(context)

    def _registrar_row(self, data):
        """Use for append some extra data into the data row."""
        return data
    # Add a flag to prevent deprecation warning, when calling this function.
    _registrar_row.prevent_warning = True  # type: ignore

    def sort_registrars(self, registrars):
        """Sort context data of registrars.

        Registrars are randomized, but sorted according to their certification score.
        """
        # Randomize order of the list of registrars and than sort it by score.
        rand = random.SystemRandom()
        rand.shuffle(registrars)
        return sorted(registrars, key=lambda row: cast(int, row["score"]), reverse=True)

    def get_context_data(self, **kwargs):
        registrars = []
        for reg in self.get_registrars():
            registrars.append(self.get_registrar_context(reg))

        kwargs.setdefault("groups", self.get_groups())
        kwargs.setdefault("registrars", self.sort_registrars(registrars))
        # Set is_retail and mark it as deprecated.
        kwargs.setdefault('is_retail', None)
        if kwargs['is_retail'] is not None:
            kwargs['is_retail'] = deprecated_context(
                kwargs['is_retail'], "Context variable is_retail is deprecated. Update your templates accordingly.")
        return super(RegistrarListMixin, self).get_context_data(**kwargs)


class RegistrarListView(RegistrarListMixin, TemplateView):
    """View with list of a registrars."""


class DownloadEvalFileView(View):
    def _serve_file(self, file_id):
        # file_info: ccReg.FileInfo(id=1, name='test.txt', path='2015/12/9/1', mimetype='text/plain', filetype=6,
        #                           crdate='2015-12-09 16:16:28.598757', size=5L)
        file_info = FILE_MANAGER.info(file_id)
        file_download = FILE_MANAGER.load(file_info.id)  # <ccReg._objref_FileDownload instance>
        try:
            file_data = file_download.download(file_info.size)
        finally:
            file_download.finalize_download()

        response = HttpResponse(content_type=file_info.mimetype)
        response['Content-Disposition'] = 'attachment; filename="%s"' % file_info.name
        response.write(file_data)
        return response

    def get(self, request, handle):
        for cert in WHOIS.get_registrar_certification_list():
            # cert: Registry.Whois.RegistrarCertification(registrar_handle='REG-FRED_A', score=2, evaluation_file_id=1L)
            if cert.registrar_handle == handle:
                return self._serve_file(cert.evaluation_file_id)
        raise Http404
