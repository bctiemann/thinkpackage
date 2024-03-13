from django.core.management.base import BaseCommand

from ims.crunchtime import CrunchtimeService

import logging
logger = logging.getLogger("crunchtime")


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--config', dest='config',)

    def handle(self, *args, **options):
        config = options.get('config', None)

        crunchtime = CrunchtimeService(config=config)
        crunchtime.process_new_purchase_orders()
