from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.views.generic import TemplateView

from webwhois.utils.corba_wrapper import CorbaWrapper, get_corba_for_module
from webwhois.views import ContactDetailMixin, ContactDetailWithMojeidMixin, DomainDetailMixin, DownloadEvalFileView, \
    KeysetDetailMixin, NssetDetailMixin, RegistrarDetailMixin, RegistrarListMixin, ResolveHandleTypeMixin, \
    WhoisFormView


def load_whois_from_idl():
    corba_name_service_client = get_corba_for_module()  # Load IDL.
    from Registry.Whois import WhoisIntf  # Module from IDL.
    return CorbaWrapper(corba_name_service_client.get_object('Whois2', WhoisIntf))


def load_filemanager_from_idl():
    corba_name_service_client = get_corba_for_module()  # Load IDL.
    from ccReg import FileManager  # Module from IDL.
    return corba_name_service_client.get_object('FileManager', FileManager)


CORBA = SimpleLazyObject(lambda: get_corba_for_module())
WHOIS = SimpleLazyObject(load_whois_from_idl)
FILEMANAGER = SimpleLazyObject(load_filemanager_from_idl)


class CorbaWhoisBaseMixin(object):

    base_template = "base_site_example.html"

    def __init__(self, *args, **kwargs):
        super(CorbaWhoisBaseMixin, self).__init__(*args, **kwargs)
        self._CORBA = CORBA
        self._WHOIS = WHOIS

    def get_context_data(self, **kwargs):
        kwargs.setdefault("base_template", self.base_template)
        return super(CorbaWhoisBaseMixin, self).get_context_data(**kwargs)


class WebwhoisFormView(CorbaWhoisBaseMixin, WhoisFormView):
    template_name = "webwhois_in_cms/form_whois.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("WHOIS_SEARCH_ENGINES", settings.WEBWHOIS_SEARCH_ENGINES)
        kwargs.setdefault("managed_zone_list", self._WHOIS.get_managed_zone_list())
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
        self._dobradomena_dict = {
            'REG-FRED_A': 'http://fred-a.dobradomena.cz/manual.pdf',
            'REG-FRED_B': 'http://fred-b.dobradomena.cz/manual.pdf',
        }
        return super(DobradomaneRegistrarListView, self).get_context_data(**kwargs)


class WebwhoisDownloadEvalFileView(CorbaWhoisBaseMixin, DownloadEvalFileView):

    def __init__(self, *args, **kwargs):
        super(WebwhoisDownloadEvalFileView, self).__init__(*args, **kwargs)
        self._FILE = FILEMANAGER
