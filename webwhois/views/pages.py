from __future__ import unicode_literals

from django.views.generic import TemplateView

from webwhois.settings import WEBWHOIS_SEARCH_ENGINES
from webwhois.utils import WHOIS
from webwhois.views import BlockObjectFormView, ContactDetailMixin, CustomEmailView, DomainDetailMixin, \
    DownloadEvalFileView, EmailInRegistryView, KeysetDetailMixin, NotarizedLetterView, NssetDetailMixin, \
    PersonalInfoFormView, PublicResponseNotFoundView, RegistrarDetailMixin, RegistrarListMixin, \
    ResolveHandleTypeMixin, SendPasswordFormView, ServeNotarizedLetterView, ServeRecordStatementView, \
    UnblockObjectFormView, WhoisFormView


class BaseTemplateMixin(object):

    base_template = "base_site_example.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("base_template", self.base_template)
        return super(BaseTemplateMixin, self).get_context_data(**kwargs)


class WebwhoisFormView(BaseTemplateMixin, WhoisFormView):
    template_name = "webwhois_in_cms/form_whois.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("WHOIS_SEARCH_ENGINES", WEBWHOIS_SEARCH_ENGINES)
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
