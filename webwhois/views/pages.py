from django.conf import settings
from django.views.generic import TemplateView

from webwhois.utils import WHOIS
from webwhois.views import ContactDetailMixin, ContactDetailWithMojeidMixin, DomainDetailMixin, DownloadEvalFileView, \
    KeysetDetailMixin, NssetDetailMixin, RegistrarDetailMixin, RegistrarListMixin, ResolveHandleTypeMixin, \
    WhoisFormView


class CorbaWhoisBaseMixin(object):

    base_template = "base_site_example.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("base_template", self.base_template)
        return super(CorbaWhoisBaseMixin, self).get_context_data(**kwargs)


class WebwhoisFormView(CorbaWhoisBaseMixin, WhoisFormView):
    template_name = "webwhois_in_cms/form_whois.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("WHOIS_SEARCH_ENGINES", settings.WEBWHOIS_SEARCH_ENGINES)
        kwargs.setdefault("managed_zone_list", WHOIS.get_managed_zone_list())
        return super(WebwhoisFormView, self).get_context_data(**kwargs)


class WebwhoisResolveHandleTypeView(CorbaWhoisBaseMixin, ResolveHandleTypeMixin, TemplateView):
    pass


class WebwhoisContactDetailView(CorbaWhoisBaseMixin, ContactDetailMixin, TemplateView):
    pass


class WebwhoisMojeidContactDetailView(CorbaWhoisBaseMixin, ContactDetailWithMojeidMixin, TemplateView):
    pass


class WebwhoisNssetDetailView(CorbaWhoisBaseMixin, NssetDetailMixin, TemplateView):
    pass


class WebwhoisKeysetDetailView(CorbaWhoisBaseMixin, KeysetDetailMixin, TemplateView):
    pass


class WebwhoisDomainDetailView(CorbaWhoisBaseMixin, DomainDetailMixin, TemplateView):
    pass


class WebwhoisRegistrarDetailView(CorbaWhoisBaseMixin, RegistrarDetailMixin, TemplateView):
    pass


class WebwhoisRegistrarListView(CorbaWhoisBaseMixin, RegistrarListMixin, TemplateView):
    pass


class DobradomaneRegistrarListView(CorbaWhoisBaseMixin, RegistrarListMixin, TemplateView):
    template_name = "webwhois_in_cms/registrar_list_with_dobradomena.html"

    def _registrar_row(self, data):
        data["dobradomena"] = self._dobradomena_dict.get(data['registrar'].handle)
        return data

    def get_context_data(self, **kwargs):
        kwargs.setdefault("HOW_TO_BECOME_A_REGISTRAR_URL", settings.WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL)
        kwargs.setdefault("REGISTRAR_CERTIFIED_FOR_RETAIL_URL", settings.WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL)
        kwargs.setdefault("REGISTRAR_SUPPORTS_DNSSEC", settings.WEBWHOIS_REGISTRAR_SUPPORTS_DNSSEC)
        kwargs.setdefault("REGISTRAR_SUPPORTS_MOJEID", settings.WEBWHOIS_REGISTRAR_SUPPORTS_MOJEID)
        kwargs.setdefault("REGISTRAR_SUPPORTS_IPV6", settings.WEBWHOIS_REGISTRAR_SUPPORTS_IPV6)
        self._dobradomena_dict = {
            'REG-FRED_A': 'http://fred-a.dobradomena.cz/manual.pdf',
            'REG-FRED_B': 'http://fred-b.dobradomena.cz/manual.pdf',
        }
        return super(DobradomaneRegistrarListView, self).get_context_data(**kwargs)


class WebwhoisDownloadEvalFileView(CorbaWhoisBaseMixin, DownloadEvalFileView):
    pass
