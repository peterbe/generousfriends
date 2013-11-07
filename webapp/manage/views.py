from decimal import Decimal

from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from django.contrib.auth import REDIRECT_FIELD_NAME

from webapp.main import utils
from webapp.main import models


def superuser_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def home(request):
    context = {}
    return render(request, 'manage/home.html', context)


@superuser_required
def dashboard(request):
    context = {}
    return render(request, 'manage/dashboard.html', context)


@superuser_required
@utils.json_view
def wishlists_data(request):
    context = {
        'wishlists': []
    }
    for wishlist in models.Wishlist.objects.all().order_by('modified'):
        count_payments = price = None
        total_amount = total_actual_amount = days_left = None
        url = reverse('manage:wishlist_data', args=(wishlist.identifier,))
        now = utils.now()
        if wishlist.verified:
            status = "VERIFIED"
        else:
            status = "NOT_VERIFIED"
        item = wishlist.get_preferred_item()
        if item:
            price = item.price
            if wishlist.verified:
                status = "VERIFIED_AND_PICKED"
                payments = models.Payment.objects.filter(item=item)
                count_payments = payments.count()
                _total_payments = payments.aggregate(Sum('amount'), Sum('actual_amount'))
                total_amount = _total_payments['amount__sum']
                total_actual_amount = _total_payments['actual_amount__sum']
                if count_payments:
                    status = "PAYMENTS_STARTED"
                    first_payment, = payments.order_by('added')[:1]
                    days_left = 30 - (now - first_payment.added).days
            identifier = item.identifier
        else:
            identifier = wishlist.identifier

        row = {
            'identifier': identifier,
            'url': url,
            'email': wishlist.email,
            'status': status,
            'verified': wishlist.verified,
            'modified': wishlist.modified,
            'added': wishlist.added,
            'price': price,
            'count_payments': count_payments,
            'total_amount': total_amount,
            'total_actual_amount': total_actual_amount,
            'days_left': days_left,
        }
        context['wishlists'].append(row)
    return context


@superuser_required
def wishlist_data(request, identifier):
    context = {}
    wishlist = get_object_or_404(models.Wishlist, identifier=identifier)
    context['wishlist'] = wishlist
    _items_preferred = (
        models.Item.objects
        .filter(wishlist=wishlist, preference__gte=1)
        .order_by('preference', '-modified')
    )
    items_preferred = []
    for item in _items_preferred:
        items_preferred.append(
            (item, models.Payment.objects.filter(item=item).order_by('added'))
        )
    context['items_preferred'] = items_preferred
    return render(request, 'manage/wishlist.html', context)
