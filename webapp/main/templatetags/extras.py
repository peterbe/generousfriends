from django import template
from django.conf import settings
from django.contrib.sites.models import RequestSite

register = template.Library()


@register.simple_tag(takes_context=True)
def full_absolute_url(context, url):
    try:
        if url.startswith('//'):
            # just need the protocol
            protocol = 'https' if context['request'].is_secure() else 'http'
            url = '%s:%s' % (protocol, url)
        elif url.startswith('/'):
            # need protocol and domain
            protocol = 'https' if context['request'].is_secure() else 'http'
            domain = RequestSite(context['request']).domain
            url = '%s://%s%s' % (protocol, domain, url)
    except Exception:
        import sys
        print sys.exc_info()
    finally:
        return url
