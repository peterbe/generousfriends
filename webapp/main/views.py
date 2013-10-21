import os
from StringIO import StringIO

import requests

from django import http
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite
from django.conf import settings
from django.core.files import File
from django.db import transaction

from . import scrape
from . import models
from . import utils
from . import forms


def start(request):
    context = {}
    return render(request, 'main/start.html', context)


@login_required
def home(request):
    pass


@utils.json_view
def wishlist_start(request):
    context = {}
    if request.method == 'POST':
        form = forms.WishlistIDForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier']
            cache_key = 'scraping-%s' % identifier
            if cache.get(cache_key):
                return {'error': 'Still working on %s' % identifier}
            admin_url = reverse('main:wishlist_admin', args=(identifier,))

            if models.Wishlist.objects.filter(identifier=identifier):
                #wishlist = models.Wishlist.objects.get(identifier=identifier)
                return {'error': 'That Wish List has already been set up'}
            cache.set(cache_key, identifier, 60)
            try:
                information = scrape.scrape(identifier)
                items = information['items']
            except scrape.NotFoundError:
                items = None

            if items:
                wishlist = models.Wishlist.objects.create(
                    identifier=identifier,
                )
                if request.user.is_authenticated():
                    wishlist.user = request.user
                    wishlist.save()
                data = {'redirect': admin_url}
                response = utils.json_response(data)
                response.set_signed_cookie(
                    'wishlist',
                    wishlist.identifier,
                    salt=settings.COOKIE_SALT,
                    max_age=60 * 60 * 24 * 7,
                    secure=request.is_secure(),
                    httponly=True
                )
                if information['name']:
                    response.set_signed_cookie(
                        'wishlist_name',
                        information['name'],
                        salt=settings.COOKIE_SALT,
                        max_age=60 * 60 * 24 * 7,
                        secure=request.is_secure(),
                        httponly=True
                    )

                return response

            elif items is None:
                return {'error': 'Could not find your Amazon.com Wish List that ID (%s)' % identifier}
            else:
                return {'error': 'No items found on Amazon.com for that ID (%s)' % identifier}
        else:
            return {'error': str(form.errors)}
    else:
        form = forms.WishlistIDForm()
    return render(request, 'main/wishlist_start.html', context)


def wishlist_home(request, identifier):
    wishlist = get_object_or_404(models.Wishlist, identifier=identifier)
    item, = models.Item.objects.filter(wishlist=wishlist, preference=1).order_by('-modified')[:1]
    if not item:
        return redirect('main:wishlist_admin', wishlist.identifier)

    if request.method == 'POST' and 'uri' in request.POST:
        form = forms.PaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            amount_cents = int(amount * 100)

            import balanced
            balanced.configure(settings.BALANCED_API_KEY)
            customer = balanced.Customer().save()
            customer.add_card(form.cleaned_data['uri'])
            customer.debit(amount=amount_cents)

            #hold = balanced.Hold(
            #    source_uri=form.cleaned_data['uri'],
            #    amount=amount_cents,
            #    description='Hold for %s (%s)' % (wishlist, item)
            #)

            models.Payment.objects.create(
                wishlist=wishlist,
                item=item,
                email=form.cleaned_data['email'],
                amount=amount,
                balanced_hash=form.cleaned_data.get('hash'),
                balanced_id=form.cleaned_data.get('id'),
            )
            data = {
                'amount': float(amount),
                'progress_amount': 21.0,
                'progress_percentage': 12
            }
            response = utils.json_response(data)
            response.set_signed_cookie(
                'contribution',
                '%s_%s_%s' % (wishlist.identifier, item.pk, amount),
                salt=settings.COOKIE_SALT,
                max_age=60 * 60 * 24 * 300,
                secure=request.is_secure(),
                httponly=True
            )
            if form.cleaned_data['email']:
                response.set_signed_cookie(
                    'email',
                    form.cleaned_data['email'],
                    salt=settings.COOKIE_SALT,
                    max_age=60 * 60 * 24 * 300,
                    secure=request.is_secure(),
                    httponly=True
                )
            return response

        else:
            return http.HttpResponseBadRequest(str(form.errors))

    try:
        cookie_identifier = request.get_signed_cookie('wishlist', salt=settings.COOKIE_SALT)
    except KeyError:
        cookie_identifier = None

    yours = False
    if cookie_identifier == wishlist.identifier:
        yours = True
        if request.user.is_authenticated() and not wishlist.user:
            wishlist.user = request.user
            wishlist.verified = True
            wishlist.save()

        if request.method == 'POST':
            if request.user.is_authenticated() and request.POST.get('first_name'):
                request.user.first_name = request.POST.get('first_name')
                request.user.save()
                return redirect('main:wishlist', wishlist.identifier)
    elif not wishlist.verified:
        return http.HttpResponse('This Wish List has not yet been verified.')

    if request.GET.get('preview'):
        yours = False

    progress_percent = 10
    progress_amount = 6.00

    absolute_url = 'https://' if request.is_secure() else 'http://'
    absolute_url += RequestSite(request).domain
    absolute_url += reverse('main:wishlist', args=(wishlist.identifier,))
    context = {
        'wishlist': wishlist,
        'item': item,
        'yours': yours,
        'absolute_url': absolute_url,
        'progress_percent': progress_percent,
        'progress_amount': progress_amount,
        'balanced_marketplace_uri': settings.BALANCED_MARKETPLACE_URI,
        'payments': models.Payment.objects.filter(wishlist=wishlist).order_by('added'),
    }
    return render(request, 'main/wishlist.html', context)


@transaction.commit_on_success
def wishlist_admin(request, identifier):
    wishlist = get_object_or_404(models.Wishlist, identifier=identifier)
    try:
        cookie_identifier = request.get_signed_cookie('wishlist', salt=settings.COOKIE_SALT)
    except KeyError:
        return http.HttpResponse('Not your Wish List')
    if cookie_identifier != wishlist.identifier:
        raise NotImplementedError
    if request.user.is_authenticated() and not wishlist.user:
        wishlist.user = request.user
        wishlist.save()

    if request.method == 'POST':
        item_id = request.POST['item']
        item = get_object_or_404(models.Item, wishlist=wishlist, id=item_id)
        # change all others first
        for other_item in models.Item.objects.filter(wishlist=wishlist).exclude(pk=item.pk, preference=0):
            other_item.preference += 1
            other_item.save()
        item.preference = 1
        item.save()
        return redirect('main:wishlist', wishlist.identifier)

    items = models.Item.objects.filter(wishlist=wishlist).order_by('added')
    if not items:
        information = scrape.scrape(wishlist.identifier)
        if information['name'] and not wishlist.name:
            wishlist.name = information['name']
            wishlist.save()
        for thing in information['items']:
            r = requests.get(thing['picture']['url'])
            filename = os.path.basename(thing['picture']['url'])
            content = File(StringIO(r.content), name=filename)

            item = models.Item.objects.create(
                wishlist=wishlist,
                title=thing['text'],
                price=thing['price'],
                url=thing['url'],
                picture=content
            )
        # try again
        items = models.Item.objects.filter(wishlist=wishlist).order_by('added')
    context = {
        'items': items,
        'wishlist': wishlist,
    }
    return render(request, 'main/wishlist_admin.html', context)


@transaction.commit_on_success
def wishlist_your_name(request, identifier):
    wishlist = get_object_or_404(models.Wishlist, identifier=identifier)
    try:
        cookie_identifier = request.get_signed_cookie('wishlist', salt=settings.COOKIE_SALT)
    except KeyError:
        return http.HttpResponse('Not your Wish List')
    if cookie_identifier != wishlist.identifier:
        raise NotImplementedError

    if request.method != 'POST':
        return redirect('main:wishlist', wishlist.identifier)

    form = forms.YourNameForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['your_email']
        name = form.cleaned_data['your_name']
        wishlist.name = name
        wishlist.email = email
        wishlist.verification_email_sent = True
        wishlist.save()
        _send_verification_email(wishlist)
        return redirect('main:wishlist', wishlist.identifier)
    else:
        return http.HttpResponse('ERROR! %s' % form.errors)


def _send_verification_email(wishlist):
