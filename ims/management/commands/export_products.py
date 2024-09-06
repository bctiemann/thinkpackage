from django.conf import settings
from django.core.management.base import BaseCommand

import sys
import csv

import logging
logger = logging.getLogger(__name__)

from ims.models import Client, Product


class Command(BaseCommand):

    csvwriter = csv.writer(sys.stdout, quoting=csv.QUOTE_MINIMAL)

    def handle(self, *args, **options):

        self.csvwriter.writerow([
            'Client',
            'Product ID',
            'Item #',
            'Name',
            'Active',
            'Dist. Center',
        ])

        for client in Client.objects.all():
            for product in client.product_set.filter(is_deleted=False):
                self.csvwriter.writerow([
                    client.company_name,
                    product.id,
                    product.item_number,
                    product.name,
                    'X' if product.is_active else '',
                    '',
                ])
