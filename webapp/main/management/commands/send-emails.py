"""This gets fired up by a cron job every few minutes"""

import datetime
from optparse import make_option

from django.core.management.base import BaseCommand

from webapp.main import models
from webapp.main import utils
from webapp.main import sending


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

        for payment in models.Payment.objects.filter(receipt_emailed__isnull=True):
            sending.send_receipt(payment, base_url)
            payment.receipt_emailed = utils.now()
            payment.save()

        # because the user makes the payment adds the message possible much
        # later we need this time_ago thing
        time_ago = utils.now() - datetime.timedelta(hours=1)
        qs = (
            models.Payment.objects
            .filter(notification_emailed__isnull=True)
            .filter(added__lt=time_ago)
        )
        for payment in qs:
            sending.send_payment_notification(payment, base_url)
            payment.notification_emailed = utils.now()
            payment.save()
