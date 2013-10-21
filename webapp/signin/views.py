from django import http
from django.core.urlresolvers import reverse
from django.utils.timezone import utc
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import transaction
from django.template.defaultfilters import slugify

from webapp.main import models

def start(request):

    context = {}
    cookie_identifier = request.get_signed_cookie('wishlist', salt=settings.COOKIE_SALT)
    if cookie_identifier and models.Wishlist.objects.filter(identifier=cookie_identifier):
        wishlist = models.Wishlist.objects.get(identifier=cookie_identifier)
        context['your_wishlist_url'] = (
            reverse('main:wishlist', args=(wishlist.identifier,))
        )
        if request.user.is_authenticated():
            return redirect(context['your_wishlist_url'])

    return render(request, 'signin/start.html', context)


def failed(request):
    context = {}
    if request.user.is_authenticated():
        return redirect('signin:start')
    return render(request, 'signin/failed.html', context)


@login_required
def done(request):
    context = {}
    context['house'] = models.House.get_house(request.user)
    return render(request, 'signin/done.html', context)


@login_required
def account(request):
    context = {}
    return render(request, 'signin/account.html', context)


@login_required
def signout(request):
    context = {}
    return render(request, 'signin/signout.html', context)


def signedout(request):
    return render(request, 'signin/signedout.html')
