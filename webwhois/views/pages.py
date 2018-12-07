#
# Copyright (C) 2015-2018  CZ.NIC, z. s. p. o.
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

from __future__ import unicode_literals

import warnings

from django.views.generic import TemplateView

from webwhois.utils import WHOIS
from webwhois.views import BlockObjectFormView, ContactDetailMixin, CustomEmailView, DomainDetailMixin, \
    DownloadEvalFileView, EmailInRegistryView, KeysetDetailMixin, NotarizedLetterView, NssetDetailMixin, \
    PersonalInfoFormView, PublicResponseNotFoundView, RegistrarDetailMixin, RegistrarListMixin, \
    ResolveHandleTypeMixin, SendPasswordFormView, ServeNotarizedLetterView, ServeRecordStatementView, \
    UnblockObjectFormView, WhoisFormView

warnings.warn("Views in `webwhois.views.pages` module are deprecated in favor of views from module `webwhois.views`.",
              DeprecationWarning)


class BaseTemplateMixin(object):

    def __init__(self, *args, **kwargs):
        warnings.warn("BaseTemplateMixin has no effect and will be removed.", DeprecationWarning)
        super(BaseTemplateMixin, self).__init__(*args, **kwargs)


class WebwhoisFormView(BaseTemplateMixin, WhoisFormView):
    template_name = "webwhois/form_whois.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("managed_zone_list", WHOIS.get_managed_zone_list())
        return super(WebwhoisFormView, self).get_context_data(**kwargs)


class WebwhoisResolveHandleTypeView(BaseTemplateMixin, ResolveHandleTypeMixin, TemplateView):
    pass


class WebwhoisContactDetailView(BaseTemplateMixin, ContactDetailMixin, TemplateView):
    pass


class WebwhoisNssetDetailView(BaseTemplateMixin, NssetDetailMixin, TemplateView):
    pass


class WebwhoisKeysetDetailView(BaseTemplateMixin, KeysetDetailMixin, TemplateView):
    pass


class WebwhoisDomainDetailView(BaseTemplateMixin, DomainDetailMixin, TemplateView):
    pass


class WebwhoisRegistrarDetailView(BaseTemplateMixin, RegistrarDetailMixin, TemplateView):
    pass


class WebwhoisRegistrarListView(BaseTemplateMixin, RegistrarListMixin, TemplateView):
    pass


class WebwhoisDownloadEvalFileView(BaseTemplateMixin, DownloadEvalFileView):
    pass


class WebwhoisPersonalInfoFormView(BaseTemplateMixin, PersonalInfoFormView):
    pass


class WebwhoisSendPasswordFormView(BaseTemplateMixin, SendPasswordFormView):
    pass


class WebwhoisBlockObjectFormView(BaseTemplateMixin, BlockObjectFormView):
    pass


class WebwhoisUnblockObjectFormView(BaseTemplateMixin, UnblockObjectFormView):
    pass


class WebwhoisPublicResponseNotFoundView(BaseTemplateMixin, PublicResponseNotFoundView):
    pass


class WebwhoisCustomEmailView(BaseTemplateMixin, CustomEmailView):
    pass


class WebwhoisEmailInRegistryView(BaseTemplateMixin, EmailInRegistryView):
    pass


class WebwhoisNotarizedLetterView(BaseTemplateMixin, NotarizedLetterView):
    pass


class WebwhoisServeNotarizedLetterView(BaseTemplateMixin, ServeNotarizedLetterView):
    pass


class WebwhoisServeRecordStatementView(BaseTemplateMixin, ServeRecordStatementView):
    pass
