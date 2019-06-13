from django.conf import settings
from django.core.management.base import BaseCommand

import sys
import csv

import logging
logger = logging.getLogger(__name__)

from ims.models import CustContact, Client


class Command(BaseCommand):

    csvwriter = csv.writer(sys.stdout, quoting=csv.QUOTE_MINIMAL)

    def add_arguments(self, parser):
        parser.add_argument('--key', dest='key',)

    def handle(self, *args, **options):

        self.csvwriter.writerow([
            'Client',
            'Location Name',
            'Address',
            'Address 2',
            'City',
            'State',
            'ZIP',
            'Contact Name',
            'Contact Email',
            'Role',
        ])

        for client in Client.objects.all():
            for location in client.location_set.all():
                self.csvwriter.writerow([
                    client.company_name,
                    location.name,
                    location.address,
                    location.address_2,
                    location.city,
                    location.state,
                    location.zip,
                    '{0} {1}'.format(location.customer_contact.first_name.strip(), location.customer_contact.last_name.strip()) if location.customer_contact else '',
                    location.customer_contact.email if location.customer_contact else '',
                    location.customer_contact.title if location.customer_contact else '',
                ])
