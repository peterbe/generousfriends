from django.conf import settings


def base(request):
    context = {}
    context['DEBUG'] = settings.DEBUG
    context['PROJECT_TITLE'] = settings.PROJECT_TITLE
    context['PROJECT_STRAPLINE'] = settings.PROJECT_STRAPLINE
    context['USE_USERSNAP'] = not settings.DEBUG
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if 'iPhone' in user_agent and 'Safari' in user_agent:
        context['USE_USERSNAP'] = False

    return context
