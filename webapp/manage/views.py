from decimal import Decimal

import balanced

from django import http
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.db import transaction

from webapp.main import utils
from webapp.main import models
from webapp.main import sending
from webapp.main import scrape
from . import forms


def almost_equal(date1, date2):
    """return true if the only difference between these two dates are
    their microseconds."""
    diff = abs(date1 - date2)
    return not diff.seconds and not diff.days


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
    context['wishlists'] = models.Wishlist.objects.all()
    context['payments'] = models.Payment.objects.all()
    return render(request, 'manage/dashboard.html', context)


@superuser_required
@utils.json_view
def dashboard_data(request):
    context = {}
    wishlists = models.Wishlist.objects.all()
    context['count_wish_lists'] = wishlists.count()
    context['count_verified_wish_lists'] = (
        wishlists.filter(verified__isnull=False).count()
    )
    items = models.Item.objects.all()
    items = items.filter(preference__gt=0)
    context['count_picked_items'] = items.count()
    context['count_complete_items'] = (
        items.filter(complete=True).count()
    )
    context['count_fulfilled_items'] = (
        items.filter(fulfilled=True).count()
    )
    context['total_priced_items'] = (
        items.aggregate(Sum('price'))['price__sum']
    )
    payments = models.Payment.objects.all()
    context['count_payments'] = payments.count()
    sums = payments.aggregate(Sum('amount'), Sum('actual_amount'))
    context['total_amount'] = sums['amount__sum']
    context['total_actual_amount'] = sums['actual_amount__sum']
    context['total_profit'] = sums['actual_amount__sum'] - sums['amount__sum']
    balanced_total_fees = (
        float(sums['amount__sum']) * (settings.BALANCED_TRANSACTION_PERCENTAGE / 100.0) +
        context['count_payments'] * float(settings.BALANCED_TRANSACTION_AMOUNT)
    )
    context['total_balanced_fees'] = utils.to_decimal(balanced_total_fees)
    context['total_profit_after_balanced'] = (
        context['total_profit'] - context['total_balanced_fees']
    )
    context['count_pageviews'] = (
        models.Pageviews.objects.all()
        .aggregate(Sum('views'))['views__sum']
    )
    return context


@superuser_required
@utils.json_view
def dashboard_news(request):
    MAX = 20

    newsitems = []

    for w in models.Wishlist.objects.all().order_by('-modified')[:MAX]:
        if w.added == w.modified:
            date = w.added
            description = 'Wish List by %s %s' % (w.name, w.email)
        else:
            date = w.modified
            description = 'Wish List updated'
            extras = []

            if w.verified and almost_equal(w.modified, w.verified):
                extras.append('verified!')
            if w.name:
                extras.append(w.name)
            if w.email:
                extras.append(w.email)
            if extras:
                description += ' (%s)' % (', '.join(extras))
        newsitems.append({
            'description': description,
            'url': reverse('manage:wishlist_data', args=(w.identifier,)),
            'date': date,
        })

    qs = (
        models.Item.objects
        .filter(preference__gt=0)
        .select_related('wishlist')
        .order_by('-modified')
    )
    for i in qs[:MAX]:
        title = i.title
        if len(title) > 60:
            title = title[:57] + '...'
        if i.added == i.modified:
            date = i.added
            description = 'Item created (%s) $%.2f' % (title, i.price)
        else:
            date = i.modified
            description = 'Item update (%s) $%.2f' % (title, i.price)
        url = reverse('manage:wishlist_data', args=(i.wishlist.identifier,))
        url += '#item-%s' % i.identifier
        newsitems.append({
            'description': description,
            'url': url,
            'date': date,
        })

    qs = (
        models.Payment.objects.all()
        .select_related('item')
        .order_by('-modified')
    )
    for p in qs[:MAX]:
        url = reverse('manage:payment_edit', args=(p.id,))
        if i.added == i.modified:
            date = i.added
            description = (
                'Payment made %s $%.2f (actually $%.2f)'
                % (p.email, p.amount, p.actual_amount)
            )
        else:
            date = i.modified
            description = (
                'Payment updated %s $%.2f (actually $%.2f)'
                % (p.name or p.email, p.amount, p.actual_amount)
            )
        newsitems.append({
            'description': description,
            'url': url,
            'date': date,
        })

    newsitems.sort(key=lambda x:x['date'], reverse=True)
    return {'newsitems': newsitems[:MAX]}


@superuser_required
def wishlists(request):
    context = {}
    context['wishlists'] = models.Wishlist.objects.all()
    return render(request, 'manage/wishlists.html', context)


@superuser_required
def payments(request):
    context = {}
    context['payments'] = models.Payment.objects.all()
    return render(request, 'manage/payments.html', context)


@superuser_required
@utils.json_view
def wishlists_data(request):
    context = {
        'wishlists': []
    }
    qs = models.Wishlist.objects.all()
    if not request.GET.get('include_not_verified', False):
        qs = qs.exclude(verified__isnull=True)
    for wishlist in qs.order_by('modified'):
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
            if item.closed:
                status = "CLOSED"
            elif wishlist.verified:
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
                    if total_amount >= item.price:
                        status = 'COMPLETE'
                        if item.fulfilled:
                            status = 'FULFILLED'
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
@utils.json_view
def payments_data(request):
    context = {
        'payments': []
    }
    qs = models.Payment.objects.all()
    for payment in qs.select_related('item').order_by('-added'):
        _item = {
            'manage_url': reverse('manage:wishlist_data', args=(payment.item.wishlist.identifier,)),
            'title': payment.item.title,
            'identifier': payment.item.identifier,
            'price': payment.item.price,
        }
        row = {
            'url': reverse('manage:payment_edit', args=(payment.id,)),
            'item': _item,
            'amount': payment.amount,
            'actual_amount': payment.actual_amount,
            'refund_amount': payment.refund_amount,
            'declined': payment.declined,
            'name': payment.name,
            'email': payment.email,
            'message': payment.message,
            'receipt_emailed': payment.receipt_emailed,
            'notification_emailed': payment.notification_emailed,
            'added': payment.added,
        }
        context['payments'].append(row)
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
        progress_amount, progress_percent = item.get_progress()
        info = {}
        info['progress_amount'] = progress_amount
        info['remaining_amount'] = item.price - progress_amount
        info['progress_percent'] = progress_percent
        info['remaining_percent'] = 100 - progress_percent
        items_preferred.append(
            (item, info, models.Payment.objects.filter(item=item).order_by('added'))
        )
    context['items_preferred'] = items_preferred
    return render(request, 'manage/wishlist.html', context)


@superuser_required
@transaction.commit_on_success
def payment_edit(request, id):
    context = {}
    payment = get_object_or_404(models.Payment, id=id)
    if request.method == 'POST':
        form = forms.PaymentEditForm(request.POST, instance=payment)
        form.fields['name'].required = False
        form.fields['message'].required = False
        refund_amount_before = payment.refund_amount
        if form.is_valid():
            refund_amount = form.cleaned_data['refund_amount']
            form.save()
            refund_amount_after = payment.refund_amount
            if refund_amount and refund_amount_after != refund_amount_before:
                balanced.configure(settings.BALANCED_API_KEY)
                debit = balanced.Debit.find(payment.balanced_uri)
                description = form.cleaned_data.get('description')
                if not description:
                    description = 'Refund for %s' % payment.item.identifier
                refund_cents = int(Decimal('100') * refund_amount_after)
                print debit.refund(
                    amount=refund_cents,
                    description=description,
                    meta={
                        'payment.id': str(payment.pk),
                        'item.identifier': payment.item.identifier,
                    }
                )
                #raise Exception(refund_amount_after)
            return redirect('manage:payments')
    else:
        form = forms.PaymentEditForm(instance=payment)
    form.fields['message'].widget.attrs['rows'] = 3
    context['form'] = form
    context['payment'] = payment
    return render(request, 'manage/payment_edit.html', context)


@superuser_required
def pageviews(request):
    context = {}
    context['pageviews'] = (
        models.Pageviews.objects.all()
        .select_related('item')
        .order_by('added')
    )
    return render(request, 'manage/pageviews.html', context)


@superuser_required
def sent_reminders(request):
    context = {}
    context['sent_reminders'] = (
        models.SentReminder.objects.all()
        .select_related('item')
        .order_by('-added')
    )
    return render(request, 'manage/sent_reminders.html', context)


@superuser_required
def sent_reminder_body(request, id):
    sent_reminder = get_object_or_404(models.SentReminder, id=id)
    return http.HttpResponse(sent_reminder.body)


@superuser_required
def send_instructions_shipping(request, identifier):
    wishlist = get_object_or_404(models.Wishlist, identifier=identifier)

    # is there a complete item that hasn't been fulfilled?
    item = None
    qs = (
        models.Item.objects
        .filter(wishlist=wishlist)
        .filter(complete=True)
        .exclude(fulfilled=True)
    )
    for item in qs:
        sending.send_instructions_shipping(item, request)
        break
    else:
        item = None
    url = reverse('manage:wishlist_data', args=(wishlist.identifier,))
    if item:
        url += '?msg=Shipping+instructions+sent'
    return redirect(url)


@superuser_required
def refetch_ship_to(request, identifier):
    wishlist = get_object_or_404(models.Wishlist, identifier=identifier)
    information = scrape.scrape(wishlist.amazon_id, shallow=True)
    url = reverse('manage:wishlist_data', args=(wishlist.identifier,))
    if information['ship_to']:
        if wishlist.ship_to != information['ship_to']:
            msg = 'Ship+to+updated!'
            wishlist.ship_to = information['ship_to']
            wishlist.save()
        else:
            msg = 'Ship+to+unchanged'
    else:
        msg = 'Ship+to+not+found'
    url += '?msg=%s' % msg
    return redirect(url)
