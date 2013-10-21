import datetime
import hashlib
import os
import unicodedata

from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import utc

from sorl.thumbnail import ImageField


def now():
    return datetime.datetime.utcnow().replace(tzinfo=utc)


class Wishlist(models.Model):
    identifier = models.CharField(max_length=20, db_index=True, unique=True)
    user = models.ForeignKey(User, null=True)
    slug = models.SlugField(null=True)
    verified = models.BooleanField(default=False)

    added = models.DateTimeField(default=now)
    modified = models.DateTimeField(default=now)

    def __str__(self):
        return self.identifier


def _upload_path(tag):
    def _upload_path_tagged(instance, filename):
        if isinstance(filename, unicode):
            filename = (
                unicodedata
                .normalize('NFD', filename)
                .encode('ascii', 'ignore')
            )
        _now = now()
        path = os.path.join(
            #"%05d" % instance.wishlist,
            _now.strftime('%Y'),
            _now.strftime('%m'),
            _now.strftime('%d')
        )
        hashed_filename = (hashlib.md5(filename +
                           str(now().microsecond)).hexdigest())
        __, extension = os.path.splitext(filename)
        return os.path.join(tag, path, hashed_filename + extension)
    return _upload_path_tagged


class Item(models.Model):
    wishlist = models.ForeignKey(Wishlist)
    title = models.CharField(max_length=200)
    url = models.URLField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    picture = ImageField(upload_to=_upload_path('pictures'))
    preference = models.IntegerField(default=0)
    added = models.DateTimeField(default=now)
    modified = models.DateTimeField(default=now)

    def __str__(self):
        return self.title


class Payment(models.Model):
    wishlist = models.ForeignKey(Wishlist)
    item = models.ForeignKey(Item)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    email = models.EmailField(null=True)
    balanced_hash = models.CharField(max_length=200, null=True)
    balanced_id = models.CharField(max_length=200, null=True)
    added = models.DateTimeField(default=now)
    modified = models.DateTimeField(default=now)


@receiver(models.signals.pre_save, sender=Wishlist)
@receiver(models.signals.pre_save, sender=Item)
@receiver(models.signals.pre_save, sender=Payment)
def update_modified(sender, instance, raw, *args, **kwargs):
    if raw:
        return
    instance.modified = now()
