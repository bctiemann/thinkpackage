from django.conf import settings
from django.core.management.base import BaseCommand

import requests
import os

import logging
logger = logging.getLogger(__name__)


URL = 'https://secure.thinkpackage.com/'
TIMEOUT_SECS = 10
RESTART_CMD = '/usr/local/etc/rc.d/apache24 graceful'


class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            response = requests.get(URL, timeout=TIMEOUT_SECS)
        except requests.exceptions.Timeout:
            logger.warning('Heartbeat timed out. Restarting service.')
            os.system(RESTART_CMD)