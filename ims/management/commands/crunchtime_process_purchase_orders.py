from django.core.management.base import BaseCommand

from ims.crunchtime import CrunchtimeService

import logging
logger = logging.getLogger("crunchtime")


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--host', dest='host',)
        parser.add_argument('--username', dest='username',)
        parser.add_argument('--password', dest='password',)
        parser.add_argument('--port', dest='port',)

    def handle(self, *args, **options):
        host = options.get('host', None)
        username = options.get('username', None)
        password = options.get('password', None)
        port = options.get('port', None)

        crunchtime = CrunchtimeService(host=host, username=username, password=password, port=port)
        crunchtime.process_new_purchase_orders()
