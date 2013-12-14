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
    ship_to = models.TextField(null=True)
    public = models.BooleanField(default=False)
    unsubscribe_reminders = models.BooleanField(default=False)
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
    title = models.CharField(max_length=400)
    url = models.URLField(max_length=400)
    affiliates_url = models.URLField(max_length=400, null=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    picture = ImageField(upload_to=utils.upload_path('pictures'))
    preference = models.IntegerField(default=0)
    complete = models.BooleanField(default=False)
    fulfilled = models.BooleanField(default=False)
    fulfilled_notes = models.TextField(null=True)
    closed = models.BooleanField(default=False)
    closed_notes = models.TextField(null=True)
    cancelled = models.DateTimeField(null=True)
    congratulation_emailed = models.DateTimeField(null=True)
    amazon_api_converted = models.BooleanField(default=True)
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
        return self.url
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
    def progress_amount(self):
        return self.get_progress()[0]

    @property
    def amount_remaining(self):
        amount, __ = self.get_progress()
        return self.price - amount

    @property
    def views(self):
        pageviews = Pageviews.objects.filter(item=self).aggregate(Sum('views'))
        if pageviews:
            return pageviews['views__sum']
        return 0


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

    @property
    def balanced_marketplace_url(self):
        uri = self.balanced_uri
        uri = uri.replace('/v1', '')
        return (
            'https://dashboard.balancedpayments.com/#%s' % uri
        )


class Verification(models.Model):
    wishlist = models.ForeignKey(Wishlist)
    email = models.EmailField()
    identifier = models.CharField(max_length=16,
                                  default=utils.identifier_maker(16))
    added = models.DateTimeField(default=utils.now)


class Pageviews(models.Model):
    item = models.ForeignKey(Item)
    views = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    added = models.DateTimeField(default=utils.now)
    modified = models.DateTimeField(default=utils.now)


class SentReminder(models.Model):
    item = models.ForeignKey(Item)
    body = models.TextField()
    to = models.EmailField()
    subject = models.TextField()
    added = models.DateTimeField(default=utils.now)
    modified = models.DateTimeField(default=utils.now)

    def __repr__(self):
        return '<%s: to:%s>' % (self.__class__.__name__, self.to)


class SplitExperiment(models.Model):
    slug = models.SlugField()
    template = models.CharField(max_length=100)
    success = models.IntegerField(default=0)
    #remote_addr = models.CharField(max_length=15)
    #user_agent = models.TextField()

    def __repr__(self):
        return '<%s: (%s, %s, %d)>' % (self.__class__.__name__, self.slug, self.template, self.success)


@receiver(models.signals.pre_save, sender=Wishlist)
@receiver(models.signals.pre_save, sender=Item)
@receiver(models.signals.pre_save, sender=Payment)
@receiver(models.signals.pre_save, sender=Pageviews)
@receiver(models.signals.pre_save, sender=SentReminder)
def update_modified(sender, instance, raw, *args, **kwargs):
    if raw:
        return
    instance.modified = utils.now()
