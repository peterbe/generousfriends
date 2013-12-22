from pprint import pprint

from django.core.management.base import BaseCommand

from webapp.main import scrape


class Command(BaseCommand):

    args = 'AMAZONID'
    def handle(self, *args, **options):
        for arg in args:
            #pprint(scrape.scrape(arg))
            scrape.scrape(arg)
