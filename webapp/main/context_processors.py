from django.conf import settings


def base(request):
    context = {}
    context['DEBUG'] = settings.DEBUG
    return context
