"""This gets fired up by a cron job every few minutes"""

import datetime
from collections import defaultdict
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db.models import Q

from webapp.main import models
from webapp.main import utils
from webapp.main import sending

MIN_DAYS = 10


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--https', action='store_true', default=False,
                    help='Put https into absolute URLs'),
        make_option('--domain', '-d', action='append', dest='domain')
    )
    args = 'domainname'
    def handle(self, domainname, **options):

        protocol = 'https' if options['https'] else 'http'
        base_url = '%s://%s' % (protocol, domainname)

        neither = (
            Q(w
        )
        items = (
            models.Item.objects
            .filter(
                preference__gt=0,
                wishlist__email__isnull=False,
                wishlist__verified=True
            )
            .exclude(Q(complete=True) | Q(closed=True))
        )

        # it has to be at least MIN_DAYS days old
        delta = datetime.timedelta(days=MIN_DAYS)
        then = utils.now() - delta
        items = items.filter(added__lt=then)

        wishlists = defaultdict(list)
        for item in items:
            assert item.wishlist.email, item
            # if it has a reminder sent in the last 10 days, skip it
            sent_reminders = (
                models.SentReminder.objects
                .filter(item=item)
                .order_by('-added')
            )
            _reminder_sent = False
            for sent_reminder in sent_reminders:
                age = utils.now() - sent_reminder.added
                if age < delta:
                    _reminder_sent = True
            if _reminder_sent:
                continue
            ## TEMPORARY
            #if item.wishlist.email not in ('cap441@gmail.com','mail@peterbe.com','ashleynbe@gmail.com'):
            #    print "TEMPORARILY SKIPPING TO", item.wishlist.email
            #    continue

            print item.id, repr(item), utils.now()-item.added
            wishlists[item.wishlist].append(item)

        for wishlist, items in wishlists.items():
            assert wishlist.email, wishlist
            sending.send_reminder(items, base_url)
