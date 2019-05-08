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
            'Email',
            'Name',
            'Role',
        ])

        for client in Client.objects.all():
            for contact in client.custcontact_set.all():
                self.csvwriter.writerow([
                    client.company_name,
                    contact.email,
                    '{0} {1}'.format(contact.first_name.strip(), contact.last_name.strip()),
                    contact.title,
                ])
