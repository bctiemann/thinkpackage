import os
import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from ims.models import Shipment


class Command(BaseCommand):

    def handle(self, *args, **options):

        shipments = Shipment.objects.all().order_by('status', '-date_created')
        shipments = shipments.filter(status=Shipment.Status.SHIPPED)

        filename = 'ShippedShipmemts.csv'

        with open('{0}/reports/{1}'.format(settings.MEDIA_ROOT, filename), mode='w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Requested Date',
                'DL #',
                'Client Name',
                'Location',
                'Total Cases',
                'Status',
                'Pallets',
            ])
            for shipment in shipments:
                writer.writerow([
                    shipment.date_created,
                    shipment.id,
                    shipment.client.company_name,
                    shipment.location.name if shipment.location else '',
                    shipment.total_cases,
                    shipment.get_status_display(),
                    ', '.join([p.pallet_id for p in shipment.pallet_set.all()]),
                ])
