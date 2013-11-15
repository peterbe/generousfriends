from django.conf import settings
from webapp.main import models


def base(request):
    context = {}
    context['DEBUG'] = settings.DEBUG
    context['PROJECT_TITLE'] = settings.PROJECT_TITLE
    context['PROJECT_STRAPLINE'] = settings.PROJECT_STRAPLINE
    context['USE_USERSNAP'] = not settings.DEBUG

    context['MOBILE'] = False
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if (
        ('iPhone' in user_agent and 'Safari' in user_agent)
        or
        ('android' in user_agent.lower() and 'AppleWebKit' in user_agent)
    ):
        context['MOBILE'] = True
    context['USE_USERSNAP'] = not context['MOBILE'] and not context['DEBUG']

    context['your_wishlists'] = None
    cookie_identifier = request.get_signed_cookie(
        'wishlist', None, salt=settings.COOKIE_SALT
    )
    if cookie_identifier:
        try:
            wishlist = models.Wishlist.objects.get(
                identifier=cookie_identifier
            )
            context['your_wishlist'] = wishlist
        except models.Wishlist.DoesNotExist:
            pass

    return context
