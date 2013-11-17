"""All things related to sending emails"""

import premailer
from html2text import html2text

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.models import RequestSite
from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest

from . import models


def _fix_base_url(base_url):
    """because most of the functions in this file can take either a
    base_url (string) or a request, we make this easy with a quick
    fixing function."""
    if isinstance(base_url, WSGIRequest):
        request = base_url
        protocol = 'https' if request.is_secure() else 'http'
        base_url = '%s://%s' % (protocol, RequestSite(request).domain)
    return base_url


def send_receipt(payment, base_url):
    base_url = _fix_base_url(base_url)

    wishlist = payment.wishlist
    item = payment.item
    context = {
        'wishlist': wishlist,
        'item': item,
        'payment': payment,
        'base_url': base_url,
        'url': reverse('main:wishlist', args=(item.identifier,)),
        'PROJECT_TITLE': settings.PROJECT_TITLE,
        'PROJECT_STRAPLINE': settings.PROJECT_STRAPLINE,
    }
    subject = (
        "Receipt for your contribution to %s's Wish List"
        % (wishlist.name or wishlist.email)
    )
    context['subject'] = subject
    html_body = render_to_string('main/_receipt.html', context)
    headers = {'Reply-To': payment.email}
    html_body = premailer.transform(
        html_body,
        base_url=base_url
    )
    body = html2text(html_body)
    email = EmailMultiAlternatives(
        subject,
        body,
        settings.WEBMASTER_FROM,
        [payment.email],
        headers=headers,
    )
    email.attach_alternative(html_body, "text/html")
    email.send()


def send_payment_notification(payment, base_url):
    base_url = _fix_base_url(base_url)

    wishlist = payment.wishlist
    item = payment.item
    context = {
        'wishlist': wishlist,
        'item': item,
        'payment': payment,
        'base_url': base_url,
        'url': reverse('main:wishlist', args=(wishlist.identifier,)),
        'PROJECT_TITLE': settings.PROJECT_TITLE,
        'PROJECT_STRAPLINE': settings.PROJECT_STRAPLINE,
    }
    subject = "Yay! A contribution on your Wish List!"
    context['subject'] = subject
    progress_amount, progress_percent = item.get_progress()
    context['progress_amount'] = progress_amount
    context['progress_percent'] = progress_percent
    context['progress_complete'] = progress_percent >= 100
    context['amount_left'] = item.price - progress_amount
    html_body = render_to_string('main/_notification.html', context)
    headers = {'Reply-To': payment.email}
    html_body = premailer.transform(
        html_body,
        base_url=base_url
    )
    body = html2text(html_body)
    email = EmailMultiAlternatives(
        subject,
        body,
        settings.WEBMASTER_FROM,
        [wishlist.email],
        headers=headers,
    )
    email.attach_alternative(html_body, "text/html")
    email.send()
    print "Sent payment notification to", wishlist.email


def send_verification_email(wishlist, base_url):
    base_url = _fix_base_url(base_url)

    verification = models.Verification.objects.create(
        wishlist=wishlist,
        email=wishlist.email,
    )
    context = {
        'wishlist': wishlist,
        'base_url': base_url,
        'url': reverse('main:wishlist_verify', args=(verification.identifier,)),
        'PROJECT_TITLE': settings.PROJECT_TITLE,
        'PROJECT_STRAPLINE': settings.PROJECT_STRAPLINE,
    }
    html_body = render_to_string('main/_verification.html', context)

    html_body = premailer.transform(
        html_body,
        base_url=base_url
    )
    body = html2text(html_body)

    headers = {'Reply-To': wishlist.email}
    subject = 'Verify your Wish List please'
    email = EmailMultiAlternatives(
        subject,
        body,
        settings.WEBMASTER_FROM,
        [wishlist.email],
        headers=headers,
    )
    email.attach_alternative(html_body, "text/html")
    email.send()
    print "Sending %r from %s to %s" % (subject, settings.WEBMASTER_FROM, wishlist.email)


def send_unable_to_scrape_error(email, name, base_url):
    base_url = _fix_base_url(base_url)

    subject = 'Your Wish List could unfortunately not be processed'
    print repr(subject), "to", (name, email)
    context = {
        'base_url': base_url,
        'subject': subject,
        'name': name,
        'PROJECT_TITLE': settings.PROJECT_TITLE,
        'PROJECT_STRAPLINE': settings.PROJECT_STRAPLINE,
    }
    html_body = render_to_string('main/_unable_to_scrape_email.html', context)

    html_body = premailer.transform(
        html_body,
        base_url=base_url
    )
    body = html2text(html_body)

    headers = {'Reply-To': email}
    email = EmailMultiAlternatives(
        subject,
        body,
        settings.WEBMASTER_FROM,
        [email],
        headers=headers,
    )
    email.attach_alternative(html_body, "text/html")
    email.send()
    print "Sent an email to", email, "about being unable to scrape"


def send_wishlist_created_email(item, base_url):
    base_url = _fix_base_url(base_url)

    subject = 'Your Wish List Has Been Set Up!'
    wishlist = item.wishlist
    context = {
        'wishlist': wishlist,
        'item': item,
        'base_url': base_url,
        'url': reverse('main:wishlist', args=(item.identifier,)),
        'subject': subject,
        'PROJECT_TITLE': settings.PROJECT_TITLE,
        'PROJECT_STRAPLINE': settings.PROJECT_STRAPLINE,
    }
    html_body = render_to_string('main/_welcome_email.html', context)

    html_body = premailer.transform(
        html_body,
        base_url=base_url
    )
    body = html2text(html_body)

    headers = {'Reply-To': wishlist.email}
    email = EmailMultiAlternatives(
        subject,
        body,
        settings.WEBMASTER_FROM,
        [wishlist.email],
        headers=headers,
    )
    email.attach_alternative(html_body, "text/html")
    email.send()


def send_share(item, recipient, base_url):
    base_url = _fix_base_url(base_url)
    wishlist = item.wishlist

    subject = "Invitation to contribute to my Wish List"
    context = {
        'wishlist': wishlist,
        'item': item,
        'base_url': base_url,
        'url': reverse('main:wishlist', args=(item.identifier,)),
        'subject': subject,
        'PROJECT_TITLE': settings.PROJECT_TITLE,
        'PROJECT_STRAPLINE': settings.PROJECT_STRAPLINE,
    }
    html_body = render_to_string('main/_share.email.html', context)

    html_body = premailer.transform(
        html_body,
        base_url=base_url
    )
    body = html2text(html_body)

    if wishlist.email != recipient:
        headers = {'Reply-To': wishlist.email}
    else:
        headers = {}
    print "RECIPIENT", repr(recipient), type(recipient)
    email = EmailMultiAlternatives(
        subject,
        body,
        settings.WEBMASTER_FROM,
        [recipient],
        headers=headers,
    )
    email.attach_alternative(html_body, "text/html")
    email.send()
