from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import models

from sorl.thumbnail import ImageField

from . import utils


class Wishlist(models.Model):
    identifier = models.CharField(max_length=20, db_index=True, unique=True)
    user = models.ForeignKey(User, null=True)
    slug = models.SlugField(null=True)
    verified = models.BooleanField(default=False)
    verification_email_sent = models.BooleanField(default=False)
    email = models.EmailField(null=True)
    name = models.CharField(max_length=100)
    mugshot = ImageField(upload_to=utils.upload_path('mugshot'))
    address = models.TextField(null=True)
    added = models.DateTimeField(default=utils.now)
    modified = models.DateTimeField(default=utils.now)

    def __str__(self):
        return self.identifier


class Item(models.Model):
    wishlist = models.ForeignKey(Wishlist)
    title = models.CharField(max_length=200)
    url = models.URLField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    picture = ImageField(upload_to=utils.upload_path('pictures'))
    preference = models.IntegerField(default=0)
    added = models.DateTimeField(default=utils.now)
    modified = models.DateTimeField(default=utils.now)

    def __str__(self):
        return self.title


class Payment(models.Model):
    wishlist = models.ForeignKey(Wishlist)
    item = models.ForeignKey(Item)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    email = models.EmailField(null=True)
    name = models.CharField(max_length=100, null=True)
    hide_name = models.BooleanField(default=False)
    message = models.TextField(null=True)
    hide_message = models.BooleanField(default=False)
    balanced_hash = models.CharField(max_length=200, null=True)
    balanced_id = models.CharField(max_length=200, null=True)
    added = models.DateTimeField(default=utils.now)
    modified = models.DateTimeField(default=utils.now)


@receiver(models.signals.pre_save, sender=Wishlist)
@receiver(models.signals.pre_save, sender=Item)
@receiver(models.signals.pre_save, sender=Payment)
def update_modified(sender, instance, raw, *args, **kwargs):
    if raw:
        return
    instance.modified = utils.now()
