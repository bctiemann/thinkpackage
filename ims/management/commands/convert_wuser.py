from django.conf import settings
from django.core.management.base import BaseCommand

import os
import unicodedata, re

import logging
logger = logging.getLogger(__name__)

from ims.models import WarehouseUser, User
from ims.cipher import AESCipher


class Command(BaseCommand):

    all_chars = (unichr(i) for i in xrange(0x110000))
    control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))

    def add_arguments(self, parser):
        parser.add_argument('--key', dest='key',)

    def remove_control_chars(self, s):
        return self.control_char_re.sub('', s)

    def handle(self, *args, **options):
        key = options.get('key', None)

        aes = AESCipher(key)

        for wuser in WarehouseUser.objects.all():
            print wuser
            password = self.remove_control_chars(aes.decrypt(wuser.password))
            name_parts = wuser.full_name.split(' ')
            first_name, last_name = name_parts[0], ''
            if len(name_parts) > 1:
                first_name = name_parts[0]
                last_name = name_parts[1]

            try:
                user = User.objects.get(email=wuser.email)
            except User.DoesNotExist:
                print('Creating {0}'.format(wuser.email))
                user = User.objects.create_user(
                    email = wuser.email,
                    password = password,
                )
                user.first_name = first_name
                user.last_name = last_name

                if wuser.role == 'warehouse':
                    user.is_warehouse = True
                elif wuser.role == 'accounting':
                    user.is_accounting = True
                user.save()
