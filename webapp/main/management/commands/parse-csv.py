import datetime
import csv
import re

from django.core.management.base import BaseCommand

from webapp.main import models

identifier_regex = re.compile('^/(\w{8})/$')

def mkdate(datestr):
    return datetime.date(
        int(datestr[:4]),
        int(datestr[4:6]),
        int(datestr[6:])
    )


class Command(BaseCommand):

    args = 'csvfile'
    def handle(self, filepath, **options):
        dates = re.findall('(\d{8})-(\d{8})\.', filepath)
        start_date, end_date = dates[0]
        start_date = mkdate(start_date)
        end_date = mkdate(end_date)
        #print (start_date, end_date)
        total = 0
        with open(filepath) as f:
            reader = csv.reader(f)
            for line in reader:
                if len(line) != 8:
                    continue
                #print repr(line), len(line)
                path = line[0]
                views = line[1]
                found = identifier_regex.findall(path)
                if not found:
                    continue
                identifier = found[0]
                try:
                    item = models.Item.objects.get(identifier=identifier)
                except models.Item.DoesNotExist:
                    #print "SKIP", identifier
                    continue
                #print repr(item)
                #print views
                views = int(views.replace(',', ''))
                models.Pageviews.objects.create(
                    item=item,
                    views=views,
                    start_date=start_date,
                    end_date=end_date
                )
                total += views

        print "#", total
        print "between", start_date, "and", end_date
