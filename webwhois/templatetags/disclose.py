from django import template
from django.utils.translation import ugettext as _

register = template.Library()

@register.filter
def if_disclose(obj, ret=None):
    """
    Returns obj.value or ret, if obj is disclosable
    Otherwise returns defined static text
    """
    if obj.disclose:
        return obj.value if ret is None else ret
    else:
        return _('Not disclosed')

@register.filter
def disclose_class(obj):
    """
    Returns special class for not disclosable object
    """
    return '' if obj.disclose else ' class="private"'

@register.filter
def mailto(obj):
    """
    Creates mailto: link if obj is defined
    """
    return '<a href="mailto:%s">%s</a>' % (obj, obj) if obj else ''

@register.filter
def get_range(value):
    """
    Creates range from value
    """
    return range(value)

@register.filter
def get_value(dictionary, key):
    """
    Returns value of dictionary defined by key
    """
    return dictionary.get(key)
