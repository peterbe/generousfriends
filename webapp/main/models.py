import decimal

from django.dispatch import receiver
from django.db import models
from django.db.models import Sum

from sorl.thumbnail import ImageField

from . import utils


class Wishlist(models.Model):
    identifier = models.CharField(max_length=8,
                                  default=utils.identifier_maker(8))
    amazon_id = models.CharField(max_length=20, db_index=True, unique=True)
    verified = models.DateTimeField(null=True)
    email = models.EmailField(null=True)
    name = models.CharField(max_length=100)
    mugshot = ImageField(upload_to=utils.upload_path('mugshot'))
    address = models.TextField(null=True)
    public = models.BooleanField(default=False)
    added = models.DateTimeField(default=utils.now)
    modified = models.DateTimeField(default=utils.now)

    def __str__(self):
        return self.identifier

    def __repr__(self):
        return (
            '<%s: %s (%s)>' % (
                self.__class__.__name__,
                self.identifier, self.amazon_id
            )
        )

    @property
    def verification_email_sent(self):
        return bool(Verification.objects.filter(wishlist=self))

    @property
    def name_or_email(self):
        return self.name or self.email

    def get_preferred_item(self):
        qs = (
            Item.objects
            .filter(wishlist=self, preference__gte=1)
            .order_by('preference', '-modified')
        )
        for item in qs[:1]:
            return item


class Item(models.Model):
    identifier = models.CharField(max_length=8,
                                  default=utils.identifier_maker(8))
    wishlist = models.ForeignKey(Wishlist)
    title = models.CharField(max_length=200)
    url = models.URLField()
    affiliates_url = models.URLField(null=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    picture = ImageField(upload_to=utils.upload_path('pictures'))
    preference = models.IntegerField(default=0)
    complete = models.BooleanField(default=False)
    fulfilled = models.BooleanField(default=False)
    fulfilled_notes = models.TextField(null=True)
    added = models.DateTimeField(default=utils.now)
    modified = models.DateTimeField(default=utils.now)

    def __str__(self):
        return self.title

    @property
    def amount_remaining(self):
        total = Payment.objects.filter(item=self).aggregate(Sum('amount'))
        if total['amount__sum']:
            total = total['amount__sum']
            return self.price - total
        else:
            return self.price

    @property
    def affiliates_url_or_url(self):
        if self.affiliates_url:
            return self.affiliates_url
        url = self.url
        if '?' in url:
            url += '&'
        else:
            url += '?'
        url += 'tag=wislisgra-20'
        return url

    def get_progress(self):
        goal_amount = self.price
        sum_ = (
            Payment.objects
            .filter(item=self)
            .exclude(declined=True)
            .aggregate(Sum('amount'), Sum('refund_amount'))
        )
        amount = sum_['amount__sum'] or decimal.Decimal('0')
        amount -= sum_['refund_amount__sum'] or decimal.Decimal('0')
        percent = int(100 * float(amount / goal_amount))
        return amount, percent

    @property
    def progress_percent(self):
        return self.get_progress()[1]

    @property
    def amount_remaining(self):
        amount, __ = self.get_progress()
        return self.price - amount


class Payment(models.Model):
    wishlist = models.ForeignKey(Wishlist)
    item = models.ForeignKey(Item)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=5, decimal_places=2)
    hide_amount = models.BooleanField(default=False)
    email = models.EmailField(null=True)
    #hide_email = models.BooleanField(default=False)
    name = models.CharField(max_length=100, null=True)
    hide_name = models.BooleanField(default=False)
    message = models.TextField(null=True)
    hide_message = models.BooleanField(default=False)
    # this default was only necessary for South migrations
    balanced_uri = models.CharField(max_length=255, default='')
    balanced_hash = models.CharField(max_length=200, null=True)
    receipt_emailed = models.DateTimeField(null=True)
    notification_emailed = models.DateTimeField(null=True)
    refund_amount = models.DecimalField(max_digits=5, decimal_places=2,
                                        default=decimal.Decimal('0.00'))
    declined = models.BooleanField(default=False)
    added = models.DateTimeField(default=utils.now)
    modified = models.DateTimeField(default=utils.now)

    def __repr__(self):
        return (
            '<%s: $%.2f by %s on %s>' % (
                self.__class__.__name__,
                self.amount,
                self.email,
                self.item.identifier
            )
        )

    @property
    def actual_fee(self):
        return self.actual_amount - self.amount




class Verification(models.Model):
    wishlist = models.ForeignKey(Wishlist)
    email = models.EmailField()
    identifier = models.CharField(max_length=16,
                                  default=utils.identifier_maker(16))
    added = models.DateTimeField(default=utils.now)


@receiver(models.signals.pre_save, sender=Wishlist)
@receiver(models.signals.pre_save, sender=Item)
@receiver(models.signals.pre_save, sender=Payment)
def update_modified(sender, instance, raw, *args, **kwargs):
    if raw:
        return
    instance.modified = utils.now()
