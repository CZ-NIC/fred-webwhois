from __future__ import unicode_literals

import random

from django.http import Http404, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from fred_idl.Registry.Whois import INVALID_HANDLE, OBJECT_NOT_FOUND

from webwhois.settings import WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED, WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED
from webwhois.utils import FILE_MANAGER, WHOIS
from webwhois.views.base import BaseContextMixin, RegistryObjectMixin


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
        except OBJECT_NOT_FOUND:
            context["server_exception"] = {
                "title": _("Registrar not found"),
                "message": cls.message_with_handle_in_html(_("No registrar matches %s handle."), handle),
            }
        except INVALID_HANDLE:
            context["server_exception"] = cls.message_invalid_handle(handle)


class RegistrarListMixin(BaseContextMixin):
    """List of Registrars."""

    template_name = "webwhois/registrar_list.html"
    is_retail = False

    def _registrar_row(self, data):
        """Use for append some extra data into the data row."""
        return data

    def get_context_data(self, **kwargs):
        # groups: {'certified': Registry.Whois.RegistrarGroup(name='certified', members=['REG-FRED_A', 'REG-FRED_B']),
        #          ...}
        groups = {group.name: group for group in WHOIS.get_registrar_groups()}

        certified_members, uncertified_members = set(), set()
        for name in WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED:
            if name in groups:
                certified_members |= set(groups[name].members)
        for name in WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED:
            if name in groups:
                uncertified_members |= set(groups[name].members)

        # certs: {'REG-FRED_A': Registry.Whois.RegistrarCertification(registrar_handle='REG-FRED_A',
        #                                                             score=2, evaluation_file_id=1L), ...}
        certs = {cert.registrar_handle: cert for cert in WHOIS.get_registrar_certification_list()}
        registrars = []
        for reg in WHOIS.get_registrars():
            # reg: Registry.Whois.Registrar(handle='REG-FRED_A', organization='Testing registrar A', ...)
            if self.is_retail:
                if reg.handle not in certified_members:
                    continue
            else:
                if reg.handle not in uncertified_members:
                    continue
            cert = certs.get(reg.handle)
            score = cert.score if cert else 0
            registrars.append(
                self._registrar_row({"registrar": reg, "cert": cert, "score": score, "stars": range(score)}),
            )

        # Randomize order of the list of registrars and than sort it by score.
        rand = random.SystemRandom()
        rand.shuffle(registrars)

        kwargs.setdefault("groups", groups)
        kwargs.setdefault("registrars", sorted(registrars, key=lambda row: row["score"], reverse=True))
        kwargs.setdefault("is_retail", self.is_retail)
        return super(RegistrarListMixin, self).get_context_data(**kwargs)


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
