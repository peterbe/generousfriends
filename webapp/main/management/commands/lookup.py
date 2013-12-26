from pprint import pprint

import amazonproduct

from django.core.management.base import BaseCommand
from django.conf import settings

from webapp.main import scrape
from webapp.main import lookup



class Command(BaseCommand):

    args = 'AMAZONID'
    def handle(self, *args, **options):
        api = amazonproduct.API(locale='us')
        for arg in args:
            information = scrape.scrape(arg)
            #pprint(information)
            #scrape.scrape(arg)
            asins = []
            for item in information['items']:
                #if 'B002LARRDK' not in item['url']:
                #    continue
                print item['text']
                asin = lookup.url_to_asin(item['url'])
                #print "ASIN", repr(asin)
                asins.append(asin)

            looker = lookup.ItemLookup(asins)

            """
            #looker = lookup.ItemLookup(asin)
            #looker.get_affiliates_url(debug=True)
            #break
            try:
                image = looker.get_image()
            except lookup.ItemNotAccessible:
                print "\tNOT AVAILABLE"
                continue
            except:
                looker.get_image(debug=True)
                break
            try:
                url = looker.get_affiliates_url()
            except lookup.ItemNotAccessible:
                print "\tNOT AVAILABLE"
                continue
            except:
                looker.get_affiliates_url(debug=True)
                break

            print "\t", repr(image)
            print "\t", repr(url)
            print
            break
            """
