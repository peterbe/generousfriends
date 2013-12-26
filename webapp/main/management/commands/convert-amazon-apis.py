import os
from optparse import make_option
from pprint import pprint
from random import shuffle
from StringIO import StringIO

import requests

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File

from webapp.main import models
from webapp.main import lookup



class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--max', '-m', action='store', default=5,
                    help='Max number of conversions'),
    )

    def handle(self, *args, **options):
        self.converts = 0
        wishlists = set()
        qs = models.Item.objects.filter(amazon_api_converted=False)
        for item in qs:
            wishlists.add(item.wishlist)
        wishlists = list(wishlists)
        shuffle(wishlists)
        for wishlist in wishlists:
            self._convert(wishlist)
            if self.converts > int(options['max']):
                print "STOPPING AT", options['max']
                break


    def _convert(self, wishlist):
        print "IDENTIFIER", wishlist.identifier, wishlist.email
        asins = {}
        for item in models.Item.objects.filter(wishlist=wishlist, amazon_api_converted=False):
            print "\t", repr(item.title[:90])
            asin = lookup.url_to_asin(item.url)
            asins[asin] = item
        try:
            self._convert_asins(asins)
        except lookup.ItemNotAccessible:
            # we have to do one at a time :(
            for asin, item in asins.items():
                if item.amazon_api_converted:
                    continue
                try:
                    self._convert_asins({asin: item})
                except lookup.ItemNotAccessible:
                    print "\t\tBAD ASIN", asin, repr(item['title'])
                    pass

    def _convert_asins(self, asins):
        print "ASINS", asins.keys()
        lookerupper = lookup.ItemLookup(asins.keys())

        for asin, item in asins.items():
            try:
                image_url = lookerupper.images[asin]
            except KeyError:
                print "SKIPPING", repr(item.title)
                continue
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
