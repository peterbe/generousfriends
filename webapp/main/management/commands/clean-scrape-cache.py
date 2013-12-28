from pprint import pprint

from django.core.management.base import BaseCommand
from django.conf import settings

from webapp.main import scrape


class Command(BaseCommand):

    def handle(self, *args, **options):
        scrape.clean_cache(10)
