from django.conf import settings
from django.core.management.base import BaseCommand

import os
import unicodedata, re

import logging
logger = logging.getLogger(__name__)

from ims.models import WarehouseUser, User
from ims.cipher import AESCipher

DEBUG = False


class Command(BaseCommand):

    all_chars = (chr(i) for i in range(0x110000))
    control_chars = ''.join(map(chr, list(range(0,32)) + list(range(127,160))))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))

    def add_arguments(self, parser):
        parser.add_argument('--key', dest='key',)

    def remove_control_chars(self, s):
        return self.control_char_re.sub('', s)

    def handle(self, *args, **options):
        key = options.get('key', None)
        if not key:
            print('Missing --key <key>')
            raise SystemExit

        aes = AESCipher(key)

        for wuser in WarehouseUser.objects.all():
            password = self.remove_control_chars(aes.decrypt(wuser.password))
            name_parts = wuser.full_name.split(' ')
            if DEBUG:
                print(wuser.full_name, password)
            first_name, last_name = name_parts[0], ''
            if len(name_parts) > 1:
                first_name = name_parts[0]
                last_name = name_parts[1]

            try:
                user = User.objects.get(email=wuser.email)
            except User.DoesNotExist:
                print(('Creating {0} ({1})'.format(wuser.email, password)))
                user = User.objects.create_user(
                    email = wuser.email,
                    password = password,
                )
            user.first_name = first_name
            user.last_name = last_name
            user.login_count = wuser.login_count
            user.last_login = wuser.last_login
            user.created_by = User.objects.get(email=wuser.created_by.email)
            user.date_joined = wuser.date_created
            user.is_active = wuser.is_active

            if wuser.role == 'warehouse':
                user.is_warehouse = True
            elif wuser.role == 'accounting':
                user.is_accounting = True
            user.save()
