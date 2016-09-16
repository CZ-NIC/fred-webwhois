import os
from urllib import urlencode

from captcha.fields import ReCaptchaField
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.translation import get_language
from django.views.generic import TemplateView, View
from django.views.static import serve

from webwhois.forms import WhoisForm
from webwhois.utils import WHOIS
from webwhois.utils.dobradomena import get_dobradomena_list
from webwhois.views import ContactDetailWithMojeidMixin, DomainDetailMixin, DownloadEvalFileView, KeysetDetailMixin, \
    NssetDetailMixin, RegistrarDetailMixin, RegistrarListMixin, ResolveHandleTypeMixin, WhoisFormView


class WhoisWithCaptchaForm(WhoisForm):
    captcha = ReCaptchaField()


class SiteMenuMixin(object):

    base_template = "base_site.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("base_template", self.base_template)
        kwargs.setdefault("page_url_name", (":".join((self.request.resolver_match.namespace, self.request.resolver_match.url_name))).lstrip(":"))
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
        return super(SiteMenuMixin, self).get_context_data(**kwargs)


def get_captcha_cache_key(request):
    return 'webwhois_captcha_limit:%s' % request.META.get('REMOTE_ADDR')


class CountCaptchaMixin(SiteMenuMixin):

    redirect_to_form = 'webwhois:form_whois'

    def dispatch(self, request, *args, **kwargs):
        cache_key = get_captcha_cache_key(request)
        used_n_times = cache.get(cache_key, 0) + 1
        cache.set(cache_key, used_n_times)
        if used_n_times > settings.WEBWHOIS_CAPTCHA_MAX_REQUESTS:
            return redirect(reverse(self.redirect_to_form, current_app=self.request.resolver_match.namespace) + "?" +
                            urlencode({"handle": kwargs.get("handle")}))
        return super(CountCaptchaMixin, self).dispatch(request, *args, **kwargs)


class HomePageView(SiteMenuMixin, TemplateView):
    template_name = "webwhois_standalone/home_page.html"


class WebwhoisFormView(SiteMenuMixin, WhoisFormView):

    template_name = "webwhois_in_cms/form_whois.html"
    captcha_limit = 'webwhois_captcha_limit:%s'

    def get_context_data(self, **kwargs):
        kwargs.setdefault("WHOIS_SEARCH_ENGINES", settings.WEBWHOIS_SEARCH_ENGINES)
        kwargs.setdefault("managed_zone_list", WHOIS.get_managed_zone_list())
        return super(WebwhoisFormView, self).get_context_data(**kwargs)

    def get_form_class(self):
        if cache.get(get_captcha_cache_key(self.request), 0) >= settings.WEBWHOIS_CAPTCHA_MAX_REQUESTS:
            return WhoisWithCaptchaForm
        return self.form_class

    def form_valid(self, form):
        if isinstance(form, WhoisWithCaptchaForm):
            cache.delete(get_captcha_cache_key(self.request))
        return super(WebwhoisFormView, self).form_valid(form)

    def form_invalid(self, form):
        key = get_captcha_cache_key(self.request)
        cache.set(key, cache.get(key, 0) + 1)
        if isinstance(form, WhoisWithCaptchaForm) and not form.errors.get('captcha'):
            cache.delete(key)
        return super(WebwhoisFormView, self).form_invalid(form)


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
        kwargs.setdefault("HOW_TO_BECOME_A_REGISTRAR_URL", settings.WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL)
        kwargs.setdefault("REGISTRAR_CERTIFIED_FOR_RETAIL_URL", settings.WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL)
        self._dobradomena_dict = get_dobradomena_list(get_language())
        return super(WebwhoisRegistrarListView, self).get_context_data(**kwargs)


class DobradomenaServeFile(View):

    def get(self, request, handle, lang):
        path = os.path.join(handle, lang, settings.WEBWHOIS_DOBRADOMENA_FILE_NAME)
        return serve(self.request, path, document_root=settings.WEBWHOIS_DOBRADOMENA_ROOT)
