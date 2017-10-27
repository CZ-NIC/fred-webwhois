from django.views.generic import TemplateView

from webwhois.settings import WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL, WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL, \
    WEBWHOIS_REGISTRAR_SUPPORTS_DNSSEC, WEBWHOIS_REGISTRAR_SUPPORTS_IPV6, WEBWHOIS_REGISTRAR_SUPPORTS_MOJEID, \
    WEBWHOIS_SEARCH_ENGINES
from webwhois.utils import WHOIS
from webwhois.views import BlockObjectFormView, ContactDetailMixin, ContactDetailWithMojeidMixin, CustomEmailView, \
    DomainDetailMixin, DownloadEvalFileView, EmailInRegistryView, KeysetDetailMixin, NotarizedLetterView, \
    NssetDetailMixin, RegistrarDetailMixin, RegistrarListMixin, ResolveHandleTypeMixin, ResponseNotFoundView, \
    SendPasswordFormView, ServeNotarizedLetterView, ServeRecordStatementView, UnblockObjectFormView, WhoisFormView


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


class WebwhoisMojeidContactDetailView(BaseTemplateMixin, ContactDetailWithMojeidMixin, TemplateView):
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


class DobradomaneRegistrarListView(BaseTemplateMixin, RegistrarListMixin, TemplateView):
    template_name = "webwhois_in_cms/registrar_list_with_dobradomena.html"

    def _registrar_row(self, data):
        data["dobradomena"] = self._dobradomena_dict.get(data['registrar'].handle)
        return data

    def get_context_data(self, **kwargs):
        kwargs.setdefault("HOW_TO_BECOME_A_REGISTRAR_URL", WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL)
        kwargs.setdefault("REGISTRAR_CERTIFIED_FOR_RETAIL_URL", WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL)
        kwargs.setdefault("REGISTRAR_SUPPORTS_DNSSEC", WEBWHOIS_REGISTRAR_SUPPORTS_DNSSEC)
        kwargs.setdefault("REGISTRAR_SUPPORTS_MOJEID", WEBWHOIS_REGISTRAR_SUPPORTS_MOJEID)
        kwargs.setdefault("REGISTRAR_SUPPORTS_IPV6", WEBWHOIS_REGISTRAR_SUPPORTS_IPV6)
        self._dobradomena_dict = {
            'REG-FRED_A': 'http://fred-a.dobradomena.cz/manual.pdf',
            'REG-FRED_B': 'http://fred-b.dobradomena.cz/manual.pdf',
        }
        return super(DobradomaneRegistrarListView, self).get_context_data(**kwargs)


class WebwhoisDownloadEvalFileView(BaseTemplateMixin, DownloadEvalFileView):
    pass


class WebwhoisSendPasswordFormView(BaseTemplateMixin, SendPasswordFormView):
    pass


class WebwhoisBlockObjectFormView(BaseTemplateMixin, BlockObjectFormView):
    pass


class WebwhoisUnblockObjectFormView(BaseTemplateMixin, UnblockObjectFormView):
    pass


class WebwhoisResponseNotFoundView(BaseTemplateMixin, ResponseNotFoundView):
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
