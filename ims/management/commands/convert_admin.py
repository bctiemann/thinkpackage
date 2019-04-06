from django.conf import settings
from django.core.management.base import BaseCommand

import os
import unicodedata, re

import logging
logger = logging.getLogger(__name__)

from ims.models import AdminUser, User
from ims.cipher import AESCipher


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

        for admin in AdminUser.objects.all():
            try:
                password = self.remove_control_chars(aes.decrypt(admin.password))
            except TypeError:
                password = admin.password
            name_parts = admin.full_name.split(' ')
            first_name, last_name = name_parts[0], ''
            if len(name_parts) > 1:
                first_name = name_parts[0]
                last_name = name_parts[1]

            try:
                user = User.objects.get(email=admin.email)
            except User.DoesNotExist:
                print(('Creating {0} ({1})'.format(admin.email, password)))
                user = User.objects.create_user(
                    email = admin.email,
                    password = password,
                )
            user.first_name = first_name
            user.last_name = last_name
            user.date_joined = admin.date_created
            user.notes = admin.about
            user.phone_number = admin.mobile_number
            user.is_admin = True
            user.is_active = user.is_active
            user.save()

        for admin in AdminUser.objects.all():
            user = User.objects.get(email=admin.email)
            user.created_by = User.objects.get(email=admin.created_by.email)
            user.save()
