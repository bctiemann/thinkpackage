from django.conf import settings
from django.core.management.base import BaseCommand

import os
import unicodedata, re

import logging
logger = logging.getLogger(__name__)

from ims.models import User, CustContact, ClientUser, Location
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
        if not key:
            print('Missing --key <key>')
            raise SystemExit

        aes = AESCipher(key)

        for custcontact in CustContact.objects.all():
            password = self.remove_control_chars(aes.decrypt(custcontact.password))

            try:
                user = User.objects.get(email=custcontact.email)
            except User.DoesNotExist:
                print('Creating {0} ({1})'.format(custcontact.email, password))
                user = User.objects.create_user(
                    email = custcontact.email,
                    password = password,
                )
            user.first_name = custcontact.first_name
            user.last_name = custcontact.last_name
            user.phone_number = custcontact.phone_number
            user.notes = custcontact.notes
            user.last_login = custcontact.last_login
            user.is_active = custcontact.is_active
            user.save()

            print user, custcontact.client
            client_user, created = ClientUser.objects.get_or_create(
                user = user,
                client = custcontact.client,
                defaults = {
                    'title': custcontact.title,
                    'is_primary': custcontact.is_primary,
                }
            )

            for location in Location.objects.filter(customer_contact=custcontact):
                print location
                location.contact_user = client_user
                location.save()
