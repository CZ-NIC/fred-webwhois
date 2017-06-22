import os
from urllib import urlencode

from captcha.fields import ReCaptchaField
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.encoding import force_bytes
from django.utils.translation import get_language
from django.views.generic import TemplateView, View
from django.views.static import serve

from webwhois.forms import BlockObjectForm, SendPasswordForm, UnblockObjectForm, WhoisForm
from webwhois.settings import WEBWHOIS_DOBRADOMENA_FILE_NAME, WEBWHOIS_DOBRADOMENA_ROOT, \
    WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL, WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL, \
    WEBWHOIS_REGISTRAR_SUPPORTS_DNSSEC, WEBWHOIS_REGISTRAR_SUPPORTS_IPV6, WEBWHOIS_REGISTRAR_SUPPORTS_MOJEID, \
    WEBWHOIS_SEARCH_ENGINES
from webwhois.utils import WHOIS
from webwhois.utils.dobradomena import get_dobradomena_list
from webwhois.views import BlockObjectFormView, ContactDetailWithMojeidMixin, CustomEmailView, DomainDetailMixin, \
    EmailInRegistryView, KeysetDetailMixin, NotarizedLetterView, NssetDetailMixin, RegistrarDetailMixin, \
    RegistrarListMixin, ResolveHandleTypeMixin, ResponseNotFoundView, SendPasswordFormView, ServeNotarizedLetterView, \
    UnblockObjectFormView, WhoisFormView


class WhoisWithCaptchaForm(WhoisForm):
    captcha = ReCaptchaField()


class SendPasswordWithCaptchaForm(SendPasswordForm):
    captcha = ReCaptchaField()


class BlockObjectWithCaptchaForm(BlockObjectForm):
    captcha = ReCaptchaField()


class UnblockObjectWithCaptchaForm(UnblockObjectForm):
    captcha = ReCaptchaField()


class SiteMenuMixin(object):

    base_template = "base_site.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("base_template", self.base_template)
        kwargs.setdefault("page_url_name", (":".join((self.request.resolver_match.namespace,
                                                      self.request.resolver_match.url_name))).lstrip(":"))
        # The pages with selected menu item "Web whois".
        kwargs.setdefault("menu_item_whois_form", (
            "standalone_webwhois:form_whois",
            "standalone_webwhois:registry_object_type",
            "standalone_webwhois:detail_contact",
            "standalone_webwhois:detail_nsset",
            "standalone_webwhois:detail_keyset",
            "standalone_webwhois:detail_domain",
            "standalone_webwhois:detail_registrar",
        ))
        kwargs.setdefault("menu_item_public_request_form", (
            "standalone_webwhois:form_send_password",
            "standalone_webwhois:form_block_object",
            "standalone_webwhois:form_unblock_object",
        ))
        return super(SiteMenuMixin, self).get_context_data(**kwargs)


def get_captcha_cache_key(request):
    return 'webwhois_captcha_limit:%s' % request.META.get('REMOTE_ADDR')


class CountCaptchaMixin(SiteMenuMixin):

    redirect_to_form = 'webwhois:form_whois'

    def dispatch(self, request, *args, **kwargs):
        cache_key = get_captcha_cache_key(request)
        used_n_times = cache.get(cache_key, 0) + 1
        cache.set(cache_key, used_n_times)
        if used_n_times > settings.CAPTCHA_MAX_REQUESTS:
            return redirect(reverse(self.redirect_to_form, current_app=self.request.resolver_match.namespace) +
                            "?" + urlencode({"handle": force_bytes(kwargs.get("handle"))}))
        return super(CountCaptchaMixin, self).dispatch(request, *args, **kwargs)


class HomePageView(SiteMenuMixin, TemplateView):
    template_name = "webwhois_standalone/home_page.html"


class ShowFormWithCaptchaMixin(object):
    captcha_limit = 'webwhois_captcha_limit:%s'
    form_class_with_captcha = None

    def get_form_class(self):
        if cache.get(get_captcha_cache_key(self.request), 0) >= settings.CAPTCHA_MAX_REQUESTS:
            return self.form_class_with_captcha
        return self.form_class

    def form_valid(self, form):
        if isinstance(form, self.form_class_with_captcha):
            cache.delete(get_captcha_cache_key(self.request))
        return super(ShowFormWithCaptchaMixin, self).form_valid(form)

    def form_invalid(self, form):
        key = get_captcha_cache_key(self.request)
        cache.set(key, cache.get(key, 0) + 1)
        if isinstance(form, self.form_class_with_captcha) and not form.errors.get('captcha'):
            cache.delete(key)
        return super(ShowFormWithCaptchaMixin, self).form_invalid(form)


class WebwhoisFormView(SiteMenuMixin, ShowFormWithCaptchaMixin, WhoisFormView):

    template_name = "webwhois_in_cms/form_whois.html"
    form_class_with_captcha = WhoisWithCaptchaForm

    def get_context_data(self, **kwargs):
        kwargs.setdefault("WHOIS_SEARCH_ENGINES", WEBWHOIS_SEARCH_ENGINES)
        kwargs.setdefault("managed_zone_list", WHOIS.get_managed_zone_list())
        return super(WebwhoisFormView, self).get_context_data(**kwargs)


class WebwhoisResolveHandleTypeView(CountCaptchaMixin, ResolveHandleTypeMixin, TemplateView):
    pass


class WebwhoisContactDetailView(CountCaptchaMixin, ContactDetailWithMojeidMixin, TemplateView):
    pass


class WebwhoisNssetDetailView(CountCaptchaMixin, NssetDetailMixin, TemplateView):
    pass


class WebwhoisKeysetDetailView(CountCaptchaMixin, KeysetDetailMixin, TemplateView):
    pass


class WebwhoisDomainDetailView(CountCaptchaMixin, DomainDetailMixin, TemplateView):
    pass


class WebwhoisRegistrarDetailView(SiteMenuMixin, RegistrarDetailMixin, TemplateView):
    pass


class WebwhoisRegistrarListView(SiteMenuMixin, RegistrarListMixin, TemplateView):
    template_name = "webwhois_in_cms/registrar_list_with_dobradomena.html"

    def _registrar_row(self, data):
        # self._dobradomena_dict: {'REG-NIC': 'http://nic.dobradomena.cz/dobradomena/manual.pdf', ...}
        data["dobradomena"] = self._dobradomena_dict.get(data['registrar'].handle)
        return data

    def get_context_data(self, **kwargs):
        kwargs.setdefault("HOW_TO_BECOME_A_REGISTRAR_URL", WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL)
        kwargs.setdefault("REGISTRAR_CERTIFIED_FOR_RETAIL_URL", WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL)
        kwargs.setdefault("REGISTRAR_SUPPORTS_DNSSEC", WEBWHOIS_REGISTRAR_SUPPORTS_DNSSEC)
        kwargs.setdefault("REGISTRAR_SUPPORTS_MOJEID", WEBWHOIS_REGISTRAR_SUPPORTS_MOJEID)
        kwargs.setdefault("REGISTRAR_SUPPORTS_IPV6", WEBWHOIS_REGISTRAR_SUPPORTS_IPV6)
        self._dobradomena_dict = get_dobradomena_list(get_language())
        return super(WebwhoisRegistrarListView, self).get_context_data(**kwargs)


class DobradomenaServeFile(View):

    def get(self, request, handle, lang):
        path = os.path.join(handle, lang, WEBWHOIS_DOBRADOMENA_FILE_NAME)
        return serve(self.request, path, document_root=WEBWHOIS_DOBRADOMENA_ROOT)


class WebwhoisSendPasswordFormView(SiteMenuMixin, ShowFormWithCaptchaMixin, SendPasswordFormView):
    template_name = "webwhois_in_cms/form_send_password.html"
    redirect_to_form = 'webwhois:form_send_password'
    form_class_with_captcha = SendPasswordWithCaptchaForm


class WebwhoisBlockObjectFormView(SiteMenuMixin, ShowFormWithCaptchaMixin, BlockObjectFormView):
    template_name = "webwhois_in_cms/form_block_object.html"
    redirect_to_form = 'webwhois:form_block_object'
    form_class_with_captcha = BlockObjectWithCaptchaForm


class WebwhoisUnblockObjectFormView(SiteMenuMixin, ShowFormWithCaptchaMixin, UnblockObjectFormView):
    template_name = "webwhois_in_cms/form_unblock_object.html"
    redirect_to_form = 'webwhois:form_unblock_object'
    form_class_with_captcha = UnblockObjectWithCaptchaForm


class WebwhoisResponseNotFoundView(CountCaptchaMixin, ResponseNotFoundView):
    pass


class WebwhoisCustomEmailView(CountCaptchaMixin, CustomEmailView):

    def get_context_data(self, **kwargs):
        kwargs.setdefault('company_email', 'podpora@nic.cz')
        kwargs.setdefault('company_website', 'www.nic.cz')
        return super(WebwhoisCustomEmailView, self).get_context_data(**kwargs)


class WebwhoisEmailInRegistryView(CountCaptchaMixin, EmailInRegistryView):
    pass


class WebwhoisNotarizedLetterView(CountCaptchaMixin, NotarizedLetterView):
    template_name = 'webwhois_in_cms/public_request_notarized_letter.html'


class WebwhoisServeNotarizedLetterView(CountCaptchaMixin, ServeNotarizedLetterView):
    pass
