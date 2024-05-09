from datetime import date, timedelta, datetime

from django.core.management.base import BaseCommand

from ims.models import Shipment


class Command(BaseCommand):
    START_DATE = date(2013, 1, 1)

    def add_arguments(self, parser):
        parser.add_argument('--days', dest='days',)

    @staticmethod
    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days) + 1):
            yield start_date + timedelta(n)

    def handle(self, *args, **options):
        days = options.get('days', None)

        if days:
            start_date = date.today() - timedelta(days=int(days))
        else:
            start_date = Shipment.objects.order_by('date_created').first().date_created.date()
        end_date = datetime.now().date()

        shipments_per_day = {}
        for single_date in self.daterange(start_date, end_date):
            print(single_date)
            shipments = Shipment.objects.filter(date_created__date=single_date)
            shipments_per_day[single_date] = shipments.count()

        for single_date, num_shipments in shipments_per_day.items():
            print(f'{single_date.strftime("%Y-%m-%d %a")}\t{num_shipments}')
