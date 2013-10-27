from django.conf import settings


def base(request):
    context = {}
    context['DEBUG'] = settings.DEBUG
    context['PROJECT_TITLE'] = settings.PROJECT_TITLE
    context['PROJECT_STRAPLINE'] = settings.PROJECT_STRAPLINE
    return context
