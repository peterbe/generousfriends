import os
import tempfile
import shutil
import json
from decimal import Decimal

import mock
from nose.tools import eq_, ok_

from django.core import mail
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.cache import cache

from django.test import TestCase

from webapp.main import models
from webapp.main import utils


_HERE = os.path.dirname(__file__)


class Response(object):
    def __init__(self, content=None, status_code=200):
        self.content = content
        self.text = content
        self.status_code = status_code


class TestViews(TestCase):

    def setUp(self):
        super(TestViews, self).setUp()
        self.tempdir = tempfile.mkdtemp()
        settings.CACHE_DIR = self.tempdir

    def tearDown(self):
        super(TestViews, self).tearDown()
        shutil.rmtree(self.tempdir)
        cache.clear()

    @mock.patch('requests.get')
    def test_basic_run(self, rget):

        def mocked_get(url, **options):
            if 'VALIDBUTEMPTY' in url:
                return Response("<html>Nothing</html>")
            if 'VALIDBUT404S' in url:
                return Response('not found', status_code=404)
            if 'PERFECTLYVALID' in url:
                return Response("""
                <html>
                <table class="g-compact-items">
                <tr>
                  <td class="g-price"><span>12.40</span></td>
                  <td class="g-title"><a href="OTHERURL1">A Nice Thing</a></td>
                </tr>
                <tr>
                  <td class="g-price"><span>99.00</span></td>
                  <td class="g-title"><a href="OTHERURL2">A More Expensive Thing</a></td>
                </tr>

                </table>
                </html>
                """)
            if 'OTHERURL1' in url:
                return Response("""
                <html>

                </html>
                """)
            if 'OTHERURL2' in url:
                return Response("""
                <html>

                </html>
                """)
            raise NotImplementedError(url)

        rget.side_effect = mocked_get

        url = reverse('main:start')
        response = self.client.get(url)
        eq_(response.status_code, 200)

        url = reverse('main:wishlist_start')
        ok_(url in response.content)

        response = self.client.get(url)
        eq_(response.status_code, 200)

        response = self.client.post(url, {'amazon_id': 'bogus'})
        eq_(response.status_code, 200)

        structure = json.loads(response.content)
        ok_(structure['error'])

        response = self.client.post(url, {'amazon_id': 'VALIDBUTEMPTY'})
        eq_(response.status_code, 200)
        structure = json.loads(response.content)
        ok_('No items found' in structure['error'])

        response = self.client.post(url, {'amazon_id': 'VALIDBUT404S'})
        eq_(response.status_code, 200)
        structure = json.loads(response.content)
        ok_('Could not find' in structure['error'])

        response = self.client.post(url, {'amazon_id': 'PERFECTLYVALID'})
        eq_(response.status_code, 200)
        structure = json.loads(response.content)
        ok_(structure['redirect'])
        wishlist, = models.Wishlist.objects.all()
        admin_url = reverse('main:wishlist_pick_one', args=(wishlist.identifier,))
        eq_(structure['redirect'], admin_url)

        # Go there
        response = self.client.get(admin_url)
        eq_(response.status_code, 200)
        # but note that this takes use to a page the redirects
        #print response.content
        ok_('Preparing your Wish List' in response.content)
        # there's a piece of javascript in there that redirects too...
        pick_one_url_nice = reverse('main:wishlist_pick_one', args=(wishlist.identifier,))
        pick_one_url_nice += '?niceredirect=1'
        ok_(pick_one_url_nice in response.content)
        # Now pretend we're following the redirect in client-side
        response = self.client.get(pick_one_url_nice)
        eq_(response.status_code, 200)

        ok_('A Nice Thing' in response.content)
        ok_('A More Expensive Thing' in response.content)
        eq_(
            [x.preference for x in models.Item.objects.filter(wishlist=wishlist)],
            [0, 0]
        )
        ok_(models.Item.objects.get(title='A Nice Thing'))
        ok_(models.Item.objects.get(title='A More Expensive Thing'))

        # and pick one
        item = models.Item.objects.get(title='A Nice Thing')
        response = self.client.post(admin_url, {'item': item.identifier})
        url = reverse('main:wishlist', args=(item.identifier,))
        self.assertRedirects(
            response,
            url
        )
        ok_(models.Item.objects.get(title='A Nice Thing', preference=1))
        wishlist, = models.Wishlist.objects.all()
        assert not wishlist.verified

        # Go to the wishlist
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('almost ready' in response.content)

        your_name_url = reverse('main:wishlist_your_name', args=(item.identifier,))
        response = self.client.post(your_name_url, {
            'your_email': 'some@something.com',
            'your_name': 'Some Name'
        })
        self.assertRedirects(
            response,
            url
        )
        wishlist, = models.Wishlist.objects.all()
        eq_(wishlist.email, 'some@something.com')
        eq_(wishlist.name, 'Some Name')

        verification, = models.Verification.objects.filter(wishlist=wishlist)
        verify_url = reverse('main:wishlist_verify', args=(verification.identifier,))
        # check the email
        email_sent = mail.outbox[-1]
        eq_(email_sent.subject, 'Verify your Wish List please')
        ok_(verify_url in email_sent.body)

        # Follow that verification link
        response = self.client.get(verify_url)
        eq_(response.status_code, 302)
        self.assertRedirects(response, url)
        email_sent = mail.outbox[-1]
        eq_(email_sent.subject, 'Your Wish List Has Been Set Up!')
        ok_(url in email_sent.body)

        # Revisit
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('almost ready' not in response.content)

    def test_fuzzy_url(self):
        wishlist = models.Wishlist.objects.create(
            amazon_id='abc123',
            verified=utils.now(),
            email='some@email.com',
            name='Some Name',
        )
        item = models.Item.objects.create(
            wishlist=wishlist,
            title='Some Item',
            url='http://amazon.com?f=123',
            price=Decimal('99.50'),
            preference=1
        )
        url = reverse('main:wishlist', args=(item.identifier,))

        # part of the URL
        fuzzy_url = reverse('main:wishlist_fuzzy', args=(item.identifier[:4],))
        response = self.client.get(fuzzy_url)
        self.assertRedirects(response, url)

        # the wishlist identifier
        fuzzy_url = reverse('main:wishlist_fuzzy', args=(wishlist.identifier,))
        response = self.client.get(fuzzy_url)
        self.assertRedirects(response, url)

        # part of the wishlist identifier
        fuzzy_url = reverse('main:wishlist_fuzzy', args=(wishlist.identifier[:4],))
        response = self.client.get(fuzzy_url)
        self.assertRedirects(response, url)

    @mock.patch('balanced.configure')
    @mock.patch('balanced.Customer')
    def test_item_pay(self, mocked_balanced_customer, mocked_balanced_configure):
        wishlist = models.Wishlist.objects.create(
            amazon_id='abc123',
            verified=utils.now(),
            email='some@email.com',
            name='Some Name',
        )
        item = models.Item.objects.create(
            wishlist=wishlist,
            title='Some Item',
            url='http://amazon.com?f=123',
            price=Decimal('99.50'),
            preference=1
        )
        url = reverse('main:wishlist', args=(item.identifier,))
        response = self.client.get(url)
        eq_(response.status_code, 200)

        data = {
            'uri': 'SOME-URI',
            'hash': 'hashahshashas',
            'id': '999'
        }
        response = self.client.post(url, data)
        eq_(response.status_code, 200)
        structure = json.loads(response.content)
        ok_(structure['error']['amount'])
        ok_(structure['error']['email'])

        response = self.client.post(url, dict(data, amount='100.00'))
        eq_(response.status_code, 200)
        structure = json.loads(response.content)
        ok_(structure['error']['amount'])

        response = self.client.post(url, dict(data, amount='notanumber'))
        eq_(response.status_code, 200)
        structure = json.loads(response.content)
        ok_(structure['error']['amount'])

        response = self.client.post(url, dict(data, amount='0.1'))
        eq_(response.status_code, 200)
        structure = json.loads(response.content)
        ok_(structure['error']['amount'])

        data['email'] = 'normal@email.com'
        response = self.client.post(url, dict(data, amount=' $14 '))
        eq_(response.status_code, 200)
        structure = json.loads(response.content)
        eq_(structure['amount'], 14.0)
        eq_(structure['progress_amount'], 14.0)
        eq_(structure['progress_percent'], 14)
        ok_(structure['actual_amount'] > 14.0)

        payment = models.Payment.objects.get(pk=structure['payment_id'])
        eq_(payment.item, item)
        eq_(payment.wishlist, wishlist)
        ok_(payment.email)
        ok_(payment.balanced_hash)
        ok_(payment.balanced_uri)
        ok_(not payment.name)
        ok_(not payment.message)

        # a receipt was sent
        email_sent = mail.outbox[-1]
        ok_('Receipt' in email_sent.subject)
        ok_('$%.2f' % payment.amount in email_sent.body)
        ok_('$%.2f' % payment.actual_amount in email_sent.body)
        ok_(url in email_sent.body)

        # you can now supply a name and message
        your_message_url = reverse('main:wishlist_your_message', args=(item.identifier,))
        response = self.client.post(your_message_url, {
            'payment': payment.pk,
            'name': 'Mary',
            'message': ' This is my message! '
        })
        eq_(response.status_code, 200)
        structure = json.loads(response.content)
        eq_(structure, True)

        payment = models.Payment.objects.get(pk=payment.pk)
        eq_(payment.name, 'Mary')
        eq_(payment.message, 'This is my message!')

    @mock.patch('requests.get')
    def test_inbound_email(self, rget):

        def mocked_get(url, **options):
            if 'VALIDBUTEMPTY' in url:
                return Response("<html>Nothing</html>")
            if 'VALIDBUT404S' in url:
                return Response('not found', status_code=404)
            if 'PERFECTLYVALID' in url:
                return Response("""
                <html>
                <table class="g-compact-items">
                <tr>
                  <td class="g-price"><span>12.40</span></td>
                  <td class="g-title"><a href="OTHERURL1">A Nice Thing</a></td>
                </tr>
                <tr>
                  <td class="g-price"><span>99.00</span></td>
                  <td class="g-title"><a href="OTHERURL2">A More Expensive Thing</a></td>
                </tr>

                </table>
                </html>
                """)
            if 'OTHERURL1' in url:
                return Response("""
                <html>

                </html>
                """)
            if 'OTHERURL2' in url:
                return Response("""
                <html>

                </html>
                """)
            raise NotImplementedError(url)

        rget.side_effect = mocked_get

        url = reverse('main:inbound_email')
        json_file = os.path.join(_HERE, 'inbound-example.json')
        json_content = open(json_file).read()
        response = self.client.post(url, json_content, content_type="application/json")
        eq_(response.status_code, 200)

        wishlist, = models.Wishlist.objects.all()
        eq_(wishlist.email, 'mail@peterbe.com')
        eq_(wishlist.name, 'Bengtsson Peter')

        # an email is sent to verify
        email_sent = mail.outbox[-1]
        eq_(email_sent.subject, 'Verify your Wish List please')
        verification, = models.Verification.objects.filter(wishlist=wishlist)
        verify_url = reverse('main:wishlist_verify', args=(verification.identifier,))
        ok_(verify_url in email_sent.body)

        # go ahead and verify
        response = self.client.get(verify_url)
        eq_(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('main:wishlist_pick_one', args=(wishlist.identifier,))
        )
        # reload and check that it's been verified
        wishlist = models.Wishlist.objects.get(pk=wishlist.pk)
        ok_(wishlist.verified)

    @mock.patch('balanced.configure')
    @mock.patch('balanced.Customer')
    def test_total_price_email_rounding(self, mocked_balanced_customer, mocked_balanced_configure):

        wishlist = models.Wishlist.objects.create(
            amazon_id='abc123',
            verified=utils.now(),
            email='some@email.com',
            name='Some Name',
        )
        item = models.Item.objects.create(
            wishlist=wishlist,
            title='Some Item',
            url='http://amazon.com?f=123',
            price=Decimal('69.99'),
            preference=1
        )
        url = reverse('main:wishlist', args=(item.identifier,))
        response = self.client.get(url)
        eq_(response.status_code, 200)

        data = {
            'uri': 'SOME-URI',
            'hash': 'hashahshashas',
            'id': '999',
            'email': 'normal@email.com',
        }
        response = self.client.post(url, dict(data, amount='5'))
        eq_(response.status_code, 200)
        structure = json.loads(response.content)
        eq_(structure['amount'], 5.0)
        eq_(structure['progress_amount'], 5.0)
        eq_(structure['progress_percent'], 7)
        # the actual amount is expected to have 2 decimal places
        eq_(structure['actual_amount'], 6.18)
        eq_('%.2f' % structure['actual_amount'], '6.18')

    @mock.patch('requests.get')
    def test_inbound_email_failing_gracefully(self, rget):

        def mocked_get(url, **options):
            raise Exception("Some trouble")

        rget.side_effect = mocked_get

        url = reverse('main:inbound_email')
        json_file = os.path.join(_HERE, 'inbound-example.json')
        json_content = open(json_file).read()
        response = self.client.post(url, json_content, content_type="application/json")
        eq_(response.status_code, 200)

        # an email is sent to explain that it failed
        email_sent = mail.outbox[-1]
        eq_(email_sent.subject, 'Your Wish List could unfortunately not be processed')
        start_url = reverse('main:wishlist_start')
        ok_(start_url in email_sent.body)
        help_url = reverse('main:help')
        ok_(help_url in email_sent.body)
