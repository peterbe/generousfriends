from django.core.management.base import BaseCommand

from webapp.main import models


class Command(BaseCommand):

    def handle(self, **options):

        print models.Payment.objects.all()
