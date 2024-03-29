import json
import os
import decimal
import datetime
import hashlib
import urllib
from StringIO import StringIO
import sys
import traceback

import balanced
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
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Max, Sum

from . import scrape
from . import models
from . import utils
from . import forms
from . import sending
from . import lookup

def start(request):
    context = {}
    your_wishlist_identifier = request.get_signed_cookie(
        'wishlist',
        None,
        salt=settings.COOKIE_SALT
    )
    visited_items = []
    visited_identifiers = request.session.get('visited_items', [])
    _items_qs = (
        models.Item.objects.filter(identifier__in=visited_identifiers)
        .select_related('wishlist')
    )
    for item in _items_qs:
        if your_wishlist_identifier == item.wishlist.identifier:
            item.yours = True
            visited_items.append(item)
        elif item.wishlist.verified:
            item.yours = False
            visited_items.append(item)
    context['visited_items'] = visited_items
    context['sample_item'] = None
    qs = (
        models.Item.objects
        .filter(wishlist__public=True,
                preference__gt=0,
                complete=False,
                wishlist__verified__isnull=False)
        .exclude(wishlist__name='',
                 closed=True,
                 wishlist__verified__isnull=True)
        .order_by('?')
    )
    for item in qs[:1]:
        context['sample_item'] = item

    context['og_image_url'] = utils.full_absolute_url(
        request,
        settings.STATIC_URL + 'icons/icon-256.png'
    )
    context['og_image_width'] = 256
    context['og_image_height'] = 256

    experiment_slug = 'start1213'
    if your_wishlist_identifier or visited_items:
        # people from before
        experiment_slug = None
        template_ = 'main/start.html'
        print "your_wishlist_identifier", repr(your_wishlist_identifier)
        print "visited_items", repr(visited_items)
        print "Sticking to", template_
    else:
        if request.session.get(experiment_slug):
            print "\t", experiment_slug, "in session"
            template_ = request.session.get(experiment_slug)
            print "\t\t", template_
        else:
            _choices = [
                'main/start-A.html',
                'main/start-B.html',
            ]
            template_ = utils.split_choice(
                _choices,
                request.META.get('HTTP_USER_AGENT'),
                request.META.get('HTTP_ACCEPT_LANGUAGE'),
                request.META.get('REMOTE_ADDR'),
            )
            print "Randomly picked", template_
            request.session[experiment_slug] = template_
            models.SplitExperiment.objects.get_or_create(
                slug=experiment_slug,
                template=template_,
            )
    context['experiment_slug'] = experiment_slug
    return render(request, template_, context)


def handler500(request):
    import traceback
    import sys
    data = {}
    if settings.TRACEBACKS_ON_500:
        err_type, err_value, err_traceback = sys.exc_info()
        out = StringIO()
        traceback.print_exc(file=out)
        traceback_formatted = out.getvalue()
        data['err_type'] = err_type
        data['err_value'] = err_value
        data['err_traceback'] = traceback_formatted
        data['report_traceback'] = True
    else:
        data['report_traceback'] = False

    return render(request, '500.html', data, status=500)


@utils.json_view
@transaction.commit_on_success
def wishlist_start(request):
    context = {}
    if request.method == 'POST':
        return http.HttpResponse('Project has been discontinued')

        form = forms.WishlistIDForm(request.POST)
        if form.is_valid():
            amazon_id = form.cleaned_data['amazon_id']
            if models.Wishlist.objects.filter(amazon_id=amazon_id):
                wishlist = models.Wishlist.objects.get(amazon_id=amazon_id)
                if wishlist.email:
                    return {'redirect': reverse('main:wishlist_taken', args=(wishlist.identifier,))}
                else:
                    wishlist.delete()

            cache_key = 'scraping-%s' % amazon_id
            if cache.get(cache_key):
                return {'error': 'Still working on %s' % amazon_id}

            cache.set(cache_key, amazon_id, 10)
            try:
                information = scrape.scrape(amazon_id)
                items = information['items']
            except scrape.NotFoundError:
                items = None

            if items:
                wishlist = models.Wishlist.objects.create(
                    amazon_id=amazon_id,
                    ship_to=information.get('ship_to'),
                )
                name = request.get_signed_cookie('name', None, salt=settings.COOKIE_SALT)
                if name:
                    wishlist.name = name
                    wishlist.save()
                email = request.get_signed_cookie('email', None, salt=settings.COOKIE_SALT)
                if email:
                    wishlist.email = email
                    wishlist.save()

                admin_url = reverse('main:wishlist_pick_one', args=(wishlist.identifier,))
                data = {'redirect': admin_url}
                response = utils.json_response(data)
                response.set_signed_cookie(
                    'wishlist',
                    wishlist.identifier,
                    salt=settings.COOKIE_SALT,
                    max_age=60 * 60 * 24 * 300,
                    secure=request.is_secure(),
                    httponly=True
                )
                if information['name'] and not name:
                    response.set_signed_cookie(
                        'name',
                        information['name'],
                        salt=settings.COOKIE_SALT,
                        max_age=60 * 60 * 24 * 300,
                        secure=request.is_secure(),
                        httponly=True
                    )

                return response

            elif items is None:
                return {'error': 'Could not find your Amazon.com Wish List that ID (%s)' % amazon_id}
            else:
                return {'error': 'No items found on Amazon.com for that ID (%s)' % amazon_id}
        else:
            return {'error': str(form.errors)}
    else:
        form = forms.WishlistIDForm()

    experiment_slug = 'start1213'
    if request.session.get(experiment_slug):
        print "yay! you started an experiment!",
        # yay! you started an experiment!
        template_ = request.session.get(experiment_slug)
        print template_
        if not request.session.get(experiment_slug + 'complete'):
            print "You have NOT completed it"
            request.session[experiment_slug + 'complete'] = 1
            try:
                experiment = models.SplitExperiment.objects.get(
                    slug=experiment_slug,
                    template=template_
                )
                experiment.success += 1
                experiment.save()
                print "Incrmented it to", experiment.success
            except models.SplitExperiment.DoesNotExist:
                print "\tCould not find it", (experiment_slug, template_)
                pass
        else:
            print "You HAVE completed it"
    return render(request, 'main/wishlist_start.html', context)


@utils.json_view
def wishlist_home(request, identifier, fuzzy=False):
    try:
        item = models.Item.objects.select_related('wishlist').get(identifier=identifier)
        wishlist = item.wishlist
    except models.Item.DoesNotExist:
        try:
            wishlist = models.Wishlist.objects.get(identifier=identifier)
            item = None
        except models.Wishlist.DoesNotExist:
            # it's neither a wishlist or an item
            if not fuzzy:
                raise http.Http404
            _search = models.Item.objects.filter(identifier__istartswith=identifier)
            if _search.count() == 1:
                item, = _search
                return redirect('main:wishlist', item.identifier)
            _search = models.Wishlist.objects.filter(identifier__istartswith=identifier)
            if _search.count() == 1:
                wishlist, = _search
                item = None
            else:
                raise http.Http404

    if not item:
        item = wishlist.get_preferred_item()
        if not item:
            return redirect('main:wishlist_pick_one', wishlist.identifier)
        return redirect('main:wishlist', item.identifier)

    if request.method == 'POST':
        return http.HttpResponse('Project has been discontinued')

    if request.method == 'POST' and 'uri' in request.POST:
        form = forms.PaymentForm(request.POST, item=item)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            amount_cents = int(amount * 100)
            actual_amount = (
                amount +
                settings.PAYMENT_TRANSACTION_AMOUNT +
                amount * decimal.Decimal(settings.PAYMENT_TRANSACTION_PERCENTAGE / 100.0)
            )
            actual_amount = actual_amount.quantize(
                decimal.Decimal('.01'),
                rounding=decimal.ROUND_UP
            )
            cache_key = 'create-payment-%s' % form.cleaned_data['uri']
            if cache.get(cache_key):
                # oh no! A double-submission!!
                double_submission = True
                from time import sleep
                sleep(1)
                payment = models.Payment.objects.get(balanced_uri=form.cleaned_data['uri'])
            else:
                cache.set(cache_key, 1, 60)
                double_submission = False
                payment = models.Payment.objects.create(
                    wishlist=wishlist,
                    item=item,
                    email=form.cleaned_data['email'],
                    amount=amount,
                    actual_amount=actual_amount,
                    balanced_hash=form.cleaned_data.get('hash'),
                    balanced_uri=form.cleaned_data['uri'],
                )

                appears_on_statement_as = 'WishListGranted'
                description = (
                    'wishlistgranted.com %s-%s'
                    % (item.identifier, payment.pk)
                )
                balanced.configure(settings.BALANCED_API_KEY)
                customer = balanced.Customer().save()
                customer.add_card(form.cleaned_data['uri'])
                customer.debit(
                    amount=amount_cents,
                    appears_on_statement_as=appears_on_statement_as,
                    description=description,
                )

            progress_amount, progress_percent = item.get_progress()
            data = {
                'amount': float(amount),
                'actual_amount': float(actual_amount),
                'progress_amount': progress_amount,
                'progress_percent': progress_percent,
                'payment_id': payment.pk,
                'show_your_message': payment.email != item.wishlist.email,
            }
            #from pprint import pprint
            #pprint(data)
            response = utils.json_response(data)
            contribution_item = '%s_%s' % (item.pk, payment.pk)
            try:
                past_contributions = request.get_signed_cookie(
                    'contributions',
                    salt=settings.COOKIE_SALT
                )
            except KeyError:
                past_contributions = ''
            past_contributions = past_contributions.split('|')
            if contribution_item not in past_contributions:
                past_contributions.append(contribution_item)
            response.set_signed_cookie(
                'contributions',
                '|'.join(past_contributions),
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
                if not double_submission:
                    sending.send_receipt(payment, request)
                    payment.receipt_emailed = utils.now()
                    payment.save()
            return response
        else:
            return {'error': form.errors}

    cookie_identifier = request.get_signed_cookie(
        'wishlist', None, salt=settings.COOKIE_SALT
    )

    amount_remaining = None
    yours = cookie_identifier == wishlist.identifier
    if yours:
        email = wishlist.email
    else:
        email = request.get_signed_cookie('email', None, salt=settings.COOKIE_SALT)

    if request.GET.get('preview'):
        yours = False
    elif request.GET.get('amount'):
        try:
            amount_remaining = decimal.Decimal(request.GET.get('amount'))
            yours = False
        except decimal.InvalidOperation:
            return http.HttpResponse('Invalid amount')

    visited = request.session.get('visited_items', [])
    if item.identifier not in visited:
        visited.append(item.identifier)
        request.session['visited_items'] = visited

    progress_amount, progress_percent = item.get_progress()

    absolute_url = 'https://' if request.is_secure() else 'http://'
    absolute_url += RequestSite(request).domain
    absolute_url += reverse('main:wishlist', args=(item.identifier,))

    try:
        your_contributions = request.get_signed_cookie(
            'contributions',
            salt=settings.COOKIE_SALT
        )
        your_contributions = [
            x.strip() for x in your_contributions.split('|')
            if x.strip()
        ]
    except KeyError:
        your_contributions = []
    contribution_items = []

    items_map = {}
    item_pks = list(set([x.split('_')[0] for x in your_contributions]))
    if item_pks:
        items_map = dict(
            (x.pk, x) for x in models.Item.objects.filter(id__in=item_pks)
        )
    payments_map = {}
    payment_pks = list(set([x.split('_')[1] for x in your_contributions]))
    if payment_pks:
        payments_map = dict(
            (x.pk, x) for x in models.Payment.objects.filter(id__in=payment_pks)
        )
    for contribution in your_contributions:
        item_pk, payment_pk = contribution.split('_')
        try:
            _item = items_map[item_pk]
        except KeyError:
            continue
        if _item != item:
            continue
        try:
            _payment = payments_map[payment_pk]
        except KeyError:
            continue
        contribution_items.append(_payment)
    your_contributions = contribution_items

    contributions = (
        models.Payment.objects
        .filter(wishlist=wishlist, item=item)
        .exclude(declined=True)
        .order_by('added')
    )

    first_payment = None
    days_left = None
    show_days_left = True
    if contributions:
        first_payment, = contributions[:1]
        days_left = 30 - (utils.now() - first_payment.added).days
        if progress_percent >= 100:
            show_days_left = False
    else:
        show_days_left = False

    views = 0
    if yours:
        pageviews = (
            models.Pageviews.objects.filter(item=item)
            .aggregate(Sum('views'))
        )
        if pageviews:
            views = pageviews['views__sum']

    context = {
        'wishlist': wishlist,
        'item': item,
        'views': views,
        'yours': yours,
        'absolute_url': absolute_url,
        'progress_percent': progress_percent,
        'progress_amount': progress_amount,
        'progress_complete': progress_percent >= 100,
        'balanced_marketplace_uri': settings.BALANCED_MARKETPLACE_URI,
        #'payments': models.Payment.objects.filter(wishlist=wishlist).order_by('added'),
        'WEBMASTER_FROM': settings.WEBMASTER_FROM,
        'contributions': contributions,
        'PAYMENT_TRANSACTION_PERCENTAGE': settings.PAYMENT_TRANSACTION_PERCENTAGE,
        'PAYMENT_TRANSACTION_AMOUNT': settings.PAYMENT_TRANSACTION_AMOUNT,
        'email': email,
        'fee_example': get_fee_example(decimal.Decimal('15.00')),
        'contributions': contributions,
        'BALANCED_DEBUG': settings.BALANCED_DEBUG,
        'days_left': days_left,
        'first_payment': first_payment,
        'amount_remaining': amount_remaining,
        'your_contributions': your_contributions,
        'show_days_left': show_days_left,
    }

    return render(request, 'main/wishlist.html', context)


def get_fee_example(price):
    example = {
        'amount': price,
    }
    example['percentage'] = (
        example['amount'] * decimal.Decimal(settings.PAYMENT_TRANSACTION_PERCENTAGE / 100.0)
    )
    example['base'] = (
        settings.PAYMENT_TRANSACTION_AMOUNT
    )
    example['total'] = (
        example['amount'] +
        example['percentage'] +
        example['base']
    )
    example['amount_percentage'] = float(decimal.Decimal('100.') * example['amount'] / example['total'])
    example['percentage_percentage'] = float(decimal.Decimal('100.') * example['percentage'] / example['total'])
    example['base_percentage'] = float(decimal.Decimal('100.') * example['base'] / example['total'])

    return example


@transaction.commit_on_success
def wishlist_pick_one(request, identifier):
    wishlist = get_object_or_404(models.Wishlist, identifier=identifier)
    cookie_identifier = request.get_signed_cookie('wishlist', None, salt=settings.COOKIE_SALT)
    if not cookie_identifier:
        return http.HttpResponse('Not your Wish List')
    if cookie_identifier != wishlist.identifier:
        raise NotImplementedError

    if request.method == 'POST':
        return http.HttpResponse('Project has been discontinued')

        item_identifier = request.POST['item']
        item = get_object_or_404(
            models.Item,
            wishlist=wishlist,
            identifier=item_identifier
        )
        # change all others first
        for other_item in models.Item.objects.filter(wishlist=wishlist).exclude(preference=0):
            other_item.preference += 1
            other_item.save()
        item.preference = 1
        item.save()

        # do I already know your name and email?
        if wishlist.name and wishlist.email:
            # great! we can say it's verified already!
            wishlist.verified = utils.now()
            wishlist.save()
            sending.send_wishlist_created_email(item, request)

        return redirect('main:wishlist', item.identifier)

    items = models.Item.objects.filter(wishlist=wishlist).order_by('added')
    items_scraped = None
    items_skipped = []
    if not items:
        if not request.GET.get('niceredirect'):
            url = reverse('main:wishlist_pick_one', args=(wishlist.identifier,))
            url += '?niceredirect=1'
            context = {
                'url': url
            }
            return render(request, 'main/wishlist_pick_one_redirect.html', context)

        print "SCRAPING", wishlist.amazon_id
        information = scrape.scrape(wishlist.amazon_id)
        if information['name'] and not wishlist.name:
            wishlist.name = information['name']
            wishlist.save()
        if information['ship_to'] and not wishlist.ship_to:
            wishlist.ship_to = information['ship_to']
            wishlist.save()
        items_scraped = 0
        asins = []
        things = {}
        for thing in information['items']:
            if thing['price'] < settings.MIN_ITEM_PRICE:
                thing['skip_reason'] = 'Below minimum price'
                items_skipped.append(thing)
                continue
            asin = lookup.url_to_asin(thing['url'])
            asins.append(asin)
            things[asin] = thing

        lookerupper = lookup.ItemLookup(asins)

        for asin in asins:
            thing = things[asin]
            try:
                image_url = lookerupper.images[asin]
                r = requests.get(image_url)
                filename = os.path.basename(image_url)
                content = File(StringIO(r.content), name=filename)
            except KeyError:
                thing['skip_reason'] = 'Not available'
                items_skipped.append(thing)
                continue

            affiliates_url = lookerupper.affiliates_urls[asin]

            item = models.Item.objects.create(
                wishlist=wishlist,
                title=thing['text'][:400],
                price=thing['price'],
                url=thing['url'],
                affiliates_url=affiliates_url,
                picture=content
            )
            items_scraped += 1

        for thing in information['externals']:
            thing['skip_reason'] = 'Not sold by Amazon.com'
            items_skipped.append(thing)

        # try again
        items = models.Item.objects.filter(wishlist=wishlist).order_by('added')

    print "ITEMS_SCRAPED", items_scraped
    print "ITEMS_SKIPPED", items_skipped
    context = {
        'items': items,
        'wishlist': wishlist,
        'offer_refresh': False,
        'active_items': models.Item.objects.none(),
        'items_skipped': items_skipped,
    }
    return render(request, 'main/wishlist_pick_one.html', context)


@transaction.commit_on_success
def wishlist_pick_another(request, identifier):
    wishlist = get_object_or_404(models.Wishlist, identifier=identifier)
    cookie_identifier = request.get_signed_cookie('wishlist', None, salt=settings.COOKIE_SALT)
    if not cookie_identifier:
        return http.HttpResponse('Not your Wish List')
    if cookie_identifier != wishlist.identifier:
        raise NotImplementedError

    if request.method == 'POST':
        return http.HttpResponse('Project has been discontinued')

        if request.POST.get('refresh'):
            for x in models.Item.objects.filter(wishlist=wishlist, preference=0):
                assert not models.Payment.objects.filter(item=x, wishlist=wishlist)
                x.delete()
            url = reverse('main:wishlist_pick_another', args=(wishlist.identifier,))
            url += '?cleared=1'
            return utils.json_response({'redirect': url})

        item_identifier = request.POST['item']
        item = get_object_or_404(
            models.Item,
            wishlist=wishlist,
            identifier=item_identifier
        )
        max_preference = (
            models.Item.objects
            .filter(wishlist=wishlist)
            .aggregate(Max('preference'))
        )
        max_preference = max_preference['preference__max']
        item.preference = max_preference + 1
        item.save()

        # do I already know your name and email?
        if wishlist.verified:
            sending.send_wishlist_created_email(item, request)

        return redirect('main:wishlist', item.identifier)

    scraping_cache_key = 'scraping-%s' % wishlist.amazon_id

    items = models.Item.objects.filter(wishlist=wishlist, preference=0).order_by('added')
    active_items = models.Item.objects.filter(wishlist=wishlist).exclude(preference=0).order_by('added')

    items_scraped = None
    if not items:
        if cache.get(scraping_cache_key):
            return http.HttpResponse('Still working on %s' % wishlist.amazon_id)
        print "SCRAPING", wishlist.amazon_id
        cache.set(scraping_cache_key, 1, 60)
        information = scrape.scrape(wishlist.amazon_id, force_refresh=True)

        if information['name'] and not wishlist.name:
            wishlist.name = information['name']
            wishlist.save()
        if information['ship_to'] and not wishlist.ship_to:
            wishlist.ship_to = information['ship_to']
            wishlist.save()

        items_scraped = 0
        for thing in information['items']:
            if thing.get('picture'):
                r = requests.get(thing['picture']['url'])
                filename = os.path.basename(thing['picture']['url'])
                content = File(StringIO(r.content), name=filename)
            else:
                content = None

            if models.Item.objects.filter(wishlist=wishlist, title=thing['text']):
                continue

            item = models.Item.objects.create(
                wishlist=wishlist,
                title=thing['text'],
                price=thing['price'],
                url=thing['url'],
                picture=content
            )
            items_scraped += 1

        # try again
        items = models.Item.objects.filter(wishlist=wishlist).order_by('added')

    print "ITEMS_SCRAPED", items_scraped

    if cache.get(scraping_cache_key):
        offer_refresh = False
    else:
        offer_refresh = True

    context = {
        'items': items,
        'wishlist': wishlist,
        'offer_refresh': offer_refresh,
        'active_items': active_items,
        'items_skipped': None,
    }
    return render(request, 'main/wishlist_pick_one.html', context)


@transaction.commit_on_success
def wishlist_your_name(request, identifier):
    return http.HttpResponse('Project has been discontinued')
    item = get_object_or_404(models.Item, identifier=identifier)
    wishlist = item.wishlist
    try:
        cookie_identifier = request.get_signed_cookie('wishlist', salt=settings.COOKIE_SALT)
    except KeyError:
        return http.HttpResponse('Not your Wish List')
    if cookie_identifier != item.wishlist.identifier:
        raise NotImplementedError

    if request.method != 'POST':
        return redirect('main:wishlist', item.identifier)

    form = forms.YourNameForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['your_email']
        name = form.cleaned_data['your_name']
        wishlist.name = name
        wishlist.email = email
        wishlist.save()
        sending.send_verification_email(wishlist, request)
        return redirect('main:wishlist', item.identifier)
    else:
        return http.HttpResponse('ERROR! %s' % form.errors)




def wishlist_verify(request, identifier):
    verification = get_object_or_404(models.Verification, identifier=identifier)

    wishlist = verification.wishlist
    #item = verification.item
    item = wishlist.get_preferred_item()
    before = wishlist.verified
    wishlist.verified = utils.now()
    wishlist.save()
    if not before and item:
        sending.send_wishlist_created_email(item, request)
    if item:
        response = redirect('main:wishlist', item.identifier)
    else:
        url = reverse('main:wishlist_pick_one', args=(wishlist.identifier,))
        response = redirect(url)
    response.set_signed_cookie(
        'wishlist',
        wishlist.identifier,
        salt=settings.COOKIE_SALT,
        max_age=60 * 60 * 24 * 300,
        secure=request.is_secure(),
        httponly=True
    )
    return response


@transaction.commit_on_success
def wishlist_taken(request, identifier):
    wishlist = get_object_or_404(models.Wishlist, identifier=identifier)
    context = {
        'wishlist': wishlist,
    }
    if request.method == 'POST':
        return http.HttpResponse('Project has been discontinued')

        form = forms.TakenForm(request.POST, wishlist=wishlist)
        if form.is_valid():
            email = form.cleaned_data['email']
            sending.send_verification_email(wishlist, request)
            url = reverse('main:wishlist_taken', args=(wishlist.identifier,))
            return redirect(url + '?email=%s' % email)
    else:
        form = form = forms.TakenForm(wishlist=wishlist)
    context['form'] = form
    if request.GET.get('email', '').lower().strip() == wishlist.email.lower().strip():
        context['sent_to'] = request.GET['email']
        context['WEBMASTER_FROM'] = settings.WEBMASTER_FROM
    else:
        context['sent_to'] = None
    if wishlist.email:
        context['email_obfuscated'] = utils.obfuscate_email(wishlist.email)
    else:
        context['email_obfuscated'] = None
    return render(request, 'main/wishlist_taken.html', context)


def about(request):
    return render(request, 'main/about.html')


def help_page(request):
    return render(request, 'main/help.html')


def rules(request):
    return redirect('main:how_it_works', permanent=True)


def how_it_works(request):
    return render(request, 'main/how_it_works.html')


def terms(request):
    return render(request, 'main/terms.html')


def instructions_mobile(request):
    return render(request, 'main/instructions_mobile.html')


def instructions_shipping_address(request):
    return render(request, 'main/instructions_shipping_address.html')


@csrf_exempt
@transaction.commit_on_success
def inbound_email(request):
    body = request.body
    structure = json.loads(body)
    print 'Inbound email from %s' % structure['FromFull']
    root = os.path.join(settings.MEDIA_ROOT, '.inbound-emails')
    today = datetime.date.today()
    save_dir = os.path.join(root, today.strftime('%Y/%m/%d'))
    utils.mkdir(save_dir)
    filename = '%s.json' % hashlib.md5(body).hexdigest()
    filepath = os.path.join(save_dir, filename)
    log_filepath = filepath.replace('.json', '.log')
    with open(filepath, 'w') as f:
        print '\tDumping email to %s' % filepath
        json.dump(structure, f, indent=2)


    with open(log_filepath, 'w') as log:
        amazon_id = None
        scrape_error = False
        for url in utils.find_urls(structure['TextBody']):
            amazon_id = utils.find_wishlist_amazon_id(url)
            if amazon_id:
                print >>log, '\tFound amazon_id: %r' % amazon_id
                try:
                    wishlist = models.Wishlist.objects.get(amazon_id=amazon_id)
                    print >>log, '\t\tAlready exists %r' % wishlist
                    if not wishlist.email:
                        wishlist.email = structure['FromFull']['Email']
                        if not wishlist.name and structure['FromFull']['Name']:
                            wishlist.name = structure['FromFull']['Name']
                        wishlist.save()
                    sending.send_verification_email(wishlist, request)
                    print >>log, '\t\tSent verification email to %s' % wishlist.email
                    return http.HttpResponse('ok\n')
                except models.Wishlist.DoesNotExist:
                    pass

                found = {'items': []}
                # can it be scraped?
                try:
                    found = scrape.scrape(amazon_id, shallow=True)
                    print >>log, '\t\tWas able to scrape it'
                    if not found['items']:
                        print >>log, "\t\t\tUnable to find any items for", repr(amazon_id)
                except scrape.NotFoundError as not_found_error:
                    amazon_id = None
                    print >>log, '\t\tWas NOT able to scrape it'
                    exc_info, exc_value, exc_tb = sys.exc_info()
                    print >>log, "Info", exc_info
                    print >>log, "Value", exc_value
                    traceback.print_exc(log)
                except Exception:
                    print >>log, '\t\tOther scraping error'
                    exc_info, exc_value, exc_tb = sys.exc_info()
                    print >>log, "Info", exc_info
                    print >>log, "Value", exc_value
                    traceback.print_exc(file=log)
                    scrape_error = True
    print "\tDumped all logging to", log_filepath

    if amazon_id and found['items']:
        wishlist = models.Wishlist.objects.create(
            amazon_id=amazon_id,
            email=structure['FromFull']['Email'],
            name=structure['FromFull']['Name'],
            ship_to=found.get('ship_to'),
            verified=utils.now()
        )
        print 'Created Wishlist %r' % wishlist
        sending.send_verification_email(wishlist, request)
        print 'Sent verification email to %s' % wishlist.email
    else:
        sending.send_unable_to_scrape_error(
            structure['FromFull']['Email'],
            structure['FromFull']['Name'],
            request
        )
    return http.HttpResponse('ok\n')


@require_POST
@transaction.commit_on_success
def wishlist_your_message(request, identifier):
    return http.HttpResponse('Project has been discontinued')

    item = get_object_or_404(models.Item, identifier=identifier)

    payment = get_object_or_404(
        models.Payment,
        item=item,
        pk=request.POST['payment']
    )

    name = request.POST.get('name', '').strip()
    message = request.POST.get('message', '').strip()
    if name or message:
        payment.name = name
        payment.message = message
        payment.save()
    else:
        print "No name or message left this time"
    sending.send_payment_notification(payment, request)
    payment.notification_emailed = utils.now()
    payment.save()

    progress_amount, progress_percent = item.get_progress()
    if progress_amount >= item.price:
        sending.send_progress_congratulation(item, request)
        item.congratulation_emailed= utils.now()
        item.save()

    response = utils.json_response(True)
    if name:
        response.set_signed_cookie(
            'name',
            name,
            salt=settings.COOKIE_SALT,
            max_age=60 * 60 * 24 * 300,
            secure=request.is_secure(),
            httponly=True
        )
    return response



def your_admin(request):
    context = {}
    cookie_identifier = request.get_signed_cookie(
        'wishlist', None, salt=settings.COOKIE_SALT
    )

    context['your_wishlist'] = None
    if cookie_identifier:
        try:
            wishlist = models.Wishlist.objects.get(identifier=identifier)
            context['your_wishlist'] = wishlist
        except models.Wishlist.DoesNotExist:
            pass

    return render(request, 'main/your_admin.html', context)


@transaction.commit_on_success
def wishlist_settings(request, identifier):
    context = {}
    wishlist = get_object_or_404(models.Wishlist, identifier=identifier)
    cookie_identifier = request.get_signed_cookie('wishlist', None, salt=settings.COOKIE_SALT)
    if not cookie_identifier:
        return http.HttpResponse('Not your Wish List')
    if cookie_identifier != wishlist.identifier:
        return http.HttpResponse('Not your Wish List')

    context['wishlist'] = wishlist
    if request.method == 'POST':
        form = forms.WishlistAdminForm(request.POST, instance=wishlist)
        if form.is_valid():
            form.save()
            url = reverse('main:wishlist_settings', args=(wishlist.identifier,))
            url += '?msg=Changes+saved'
            return redirect(url)
    else:
        form = forms.WishlistAdminForm(instance=wishlist)
    form.fields['name'].label = 'Your Name'
    form.fields['public'].help_text = (
        'If you make your list public, it can be randomly shown on the '
        'home page as an example.'
    )
    if models.SentReminder.objects.filter(to=wishlist.email).exists():
        form.fields['unsubscribe_reminders'].help_text = (
            "If you don't want email reminders about your progress, check this box."
        )
    else:
        del form.fields['unsubscribe_reminders']
    context['form'] = form
    context['msg'] = request.GET.get('msg')
    items = (
        models.Item.objects
        .filter(wishlist=wishlist, preference__gt=0)
        .order_by('preference')
    )
    context['items'] = [
        (x, models.Payment.objects.filter(item=x))
        for x in items
    ]
    return render(request, 'main/wishlist_settings.html', context)


@require_POST
@transaction.commit_on_success
@utils.json_view
def wishlist_share_by_email(request, identifier):
    item = get_object_or_404(models.Item, identifier=identifier)
    form = forms.ShareByEmailForm(request.POST)
    if form.is_valid():
        emails = form.cleaned_data['emails']
        if not emails:
            return {'error': "No valid email addresses in that input"}
        if form.cleaned_data['send_copy']:
            emails.append(item.wishlist.email)

        for email in emails:
            email = unicode(email)
            sending.send_share(item, email, request)
        return {'emails': [unicode(x) for x in emails]}
    else:
        return {'error': form.error}


def find_wishlist(request):
    context = {}
    context['sent_to'] = request.GET.get('sent_to')
    if request.method == 'POST':
        form = forms.FindWishlistForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            wishlist = models.Wishlist.objects.get(email=email)
            sending.send_verification_email(wishlist, request)
            url = reverse('main:find_wishlist')
            url += '?' + urllib.urlencode({'sent_to': wishlist.email})
            return redirect(url)
    else:
        form = forms.FindWishlistForm()
    context['form'] = form
    context['WEBMASTER_FROM'] = settings.WEBMASTER_FROM
    return render(request, 'main/find_wishlist.html', context)


@transaction.commit_on_success
def close_item(request, identifier):
    context = {}
    item = get_object_or_404(models.Item, identifier=identifier)
    # but can you edit it?
    cookie_identifier = request.get_signed_cookie('wishlist', None, salt=settings.COOKIE_SALT)
    if not cookie_identifier:
        return http.HttpResponse('You need to prove that this is on your Wish List')
    if cookie_identifier != item.wishlist.identifier:
        return http.HttpResponse('Not your Wish List')

    if request.method == 'POST':
        form = forms.CloseItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            url = reverse('main:wishlist_settings', args=(item.wishlist.identifier,))
            url += '?msg=Item+closed'
            return redirect(url)
    else:
        form = forms.CloseItemForm(instance=item)

    form.fields['closed_notes'].widget.attrs['rows'] = 2
    context['item'] = item
    context['form'] = form
    return render(request, 'main/close_item.html', context)


def debugger(request):
    return http.HttpResponse('Your IP: %s\n' % request.META.get('REMOTE_ADDR'))
