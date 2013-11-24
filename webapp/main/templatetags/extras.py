from django import template

from webapp.main.utils import full_absolute_url as _full_absolute_url

register = template.Library()


@register.simple_tag(takes_context=True)
def full_absolute_url(context, url):
    return _full_absolute_url(context['request'], url)
