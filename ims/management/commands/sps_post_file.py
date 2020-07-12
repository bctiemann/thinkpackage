from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from ims.sps import SPSService

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--file', dest='file',)

    def handle(self, *args, **options):
        filename = options.get('file', None)
        if not filename:
            print('Missing --file <file>')
            raise SystemExit

        sps = SPSService()

        file = open(filename, "rb")
        file_data = file.read()

        bare_filename = Path(filename).name

        result = sps.create_transaction(file_data, file_key=bare_filename)
        print(result.json())
