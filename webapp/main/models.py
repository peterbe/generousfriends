import uuid

from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum

from sorl.thumbnail import ImageField

from . import utils


class Wishlist(models.Model):
    identifier = models.CharField(max_length=20, db_index=True, unique=True)
    user = models.ForeignKey(User, null=True)
    slug = models.SlugField(null=True)
    verified = models.DateTimeField(null=True)
    email = models.EmailField(null=True)
    name = models.CharField(max_length=100)
    mugshot = ImageField(upload_to=utils.upload_path('mugshot'))
    address = models.TextField(null=True)
    added = models.DateTimeField(default=utils.now)
    modified = models.DateTimeField(default=utils.now)

    def __str__(self):
        return self.identifier

    @property
    def verification_email_sent(self):
        return bool(Verification.objects.filter(wishlist=self))


class Item(models.Model):
    wishlist = models.ForeignKey(Wishlist)
    title = models.CharField(max_length=200)
    url = models.URLField()
    affiliates_url = models.URLField(null=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    picture = ImageField(upload_to=utils.upload_path('pictures'))
    preference = models.IntegerField(default=0)
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


class Payment(models.Model):
    wishlist = models.ForeignKey(Wishlist)
    item = models.ForeignKey(Item)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=5, decimal_places=2)
    email = models.EmailField(null=True)
    name = models.CharField(max_length=100, null=True)
    hide_name = models.BooleanField(default=False)
    message = models.TextField(null=True)
    hide_message = models.BooleanField(default=False)
    balanced_hash = models.CharField(max_length=200, null=True)
    balanced_id = models.CharField(max_length=200, null=True)
    added = models.DateTimeField(default=utils.now)
    modified = models.DateTimeField(default=utils.now)

    @property
    def actual_fee(self):
        return self.actual_amount - self.amount


def identifier_maker(length):
    def maker():
        return uuid.uuid4().hex[:length]
    return maker


class Verification(models.Model):
    wishlist = models.ForeignKey(Wishlist)
    email = models.EmailField()
    identifier = models.CharField(max_length=16, default=identifier_maker(16))
    added = models.DateTimeField(default=utils.now)


@receiver(models.signals.pre_save, sender=Wishlist)
@receiver(models.signals.pre_save, sender=Item)
@receiver(models.signals.pre_save, sender=Payment)
def update_modified(sender, instance, raw, *args, **kwargs):
    if raw:
        return
    instance.modified = utils.now()