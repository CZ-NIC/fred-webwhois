from django.conf import settings

# import corba modules only on production (so they don't have to be imported
# each time new fastcgi process is created, on the other hand don't import them
# on testing, because when you develop, your server is auto-reloaded each time
# you save a change in code and you want this to be fast.
if settings.LOAD_CORBA_AT_START:
    from webwhois.utils.corba_wrapper import get_corba_for_module
    get_corba_for_module()
