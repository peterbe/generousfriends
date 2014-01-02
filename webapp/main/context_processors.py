from django.conf import settings
from webapp.main import models


def base(request):
    context = {}
    context['DEBUG'] = settings.DEBUG
    context['PROJECT_TITLE'] = settings.PROJECT_TITLE
    context['PROJECT_STRAPLINE'] = settings.PROJECT_STRAPLINE
    context['GOOGLE_ANALYTICS'] = settings.USE_GOOGLE_ANALYTICS
    context['USE_USERSNAP'] = False  #not settings.DEBUG
    if '/manage/' in request.path_info:
        context['GOOGLE_ANALYTICS'] = False

    context['MOBILE'] = context['ANDROID'] = False
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if (
        ('iPhone' in user_agent and 'Safari' in user_agent)
        or
        ('android' in user_agent.lower() and 'AppleWebKit' in user_agent)
    ):
        context['MOBILE'] = True
        if 'android' in user_agent.lower():
            context['ANDROID'] = True
    context['USE_USERSNAP'] = context['USE_USERSNAP'] and not context['MOBILE'] and not context['DEBUG']
    if '/manage/' in request.path_info:
        context['USE_USERSNAP'] = False

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
