import os

from django.conf import settings
from django.core.management.base import BaseCommand

from ims.models import ShipmentDoc


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--key', dest='key',)

    def handle(self, *args, **options):

        new_prefix = 'shipment_docs'

        for shipment_doc in ShipmentDoc.objects.all():
            test_filename = os.path.join(settings.MEDIA_ROOT_LEGACY, shipment_doc.file.name)
            if os.path.isfile(test_filename):
                print(f'{test_filename} is legacy')
                old_dir = f'{settings.MEDIA_ROOT_LEGACY}/{shipment_doc.uuid}'
                new_dir = f'{settings.MEDIA_ROOT}/{new_prefix}/{shipment_doc.uuid}'
                new_filename = f'{new_prefix}/{shipment_doc.file}'
                os.rename(old_dir, new_dir)
                shipment_doc.file = new_filename
                shipment_doc.save()