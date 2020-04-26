from django.conf import settings
from django.core.management.base import BaseCommand

import os
import unicodedata, re

import logging
logger = logging.getLogger(__name__)

from ims.models import User, CustContact, ClientUser, Location
from ims.cipher import AESCipher

DEBUG = False


class Command(BaseCommand):

    all_chars = (chr(i) for i in range(0x110000))
    control_chars = ''.join(map(chr, list(range(0,32)) + list(range(127,160))))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))

    def add_arguments(self, parser):
        parser.add_argument('--key', dest='key', default=settings.CF_GLOBAL_KEY)
        parser.add_argument('--encrypted', dest='encrypted')

    def remove_control_chars(self, s):
        return self.control_char_re.sub('', s)

    def handle(self, *args, **options):
        key = options.get('key', None)
        encrypted = options.get('encrypted', None)
        if not key:
            print('Missing --key <key>')
            raise SystemExit

        aes = AESCipher(key)
        password = self.remove_control_chars(aes.decrypt(encrypted))
        print(password)
