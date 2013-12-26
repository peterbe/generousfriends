import os
from pprint import pprint
from StringIO import StringIO

import requests

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File

from webapp.main import models
from webapp.main import lookup



class Command(BaseCommand):


    def handle(self, *args, **options):
        self.converts = 0
        wishlists = set()
        qs = models.Item.objects.filter(amazon_api_converted=False)
        for item in qs:
            wishlists.add(item.wishlist)

        for wishlist in wishlists:
            self._convert(wishlist)
            if self.converts > 5:
                print "STOPPING AT 5"
                break


    def _convert(self, wishlist):
        print "IDENTIFIER", wishlist.identifier, wishlist.email
        asins = {}
        for item in models.Item.objects.filter(wishlist=wishlist, amazon_api_converted=False):
            print "\t", repr(item.title[:70])
            asin = lookup.url_to_asin(item.url)
            asins[asin] = item
        lookerupper = lookup.ItemLookup(asins.keys())

        for asin, item in asins.items():
            image_url = lookerupper.images[asin]
            print "\tDownloading", image_url[:70]
            r = requests.get(image_url)

            filename = os.path.basename(image_url)
            content = File(StringIO(r.content), name=filename)
            item.picture = content

            affiliates_url = lookerupper.affiliates_urls[asin]
            item.affiliates_url = affiliates_url

            item.amazon_api_converted = True
            item.save()

        self.converts += 1
