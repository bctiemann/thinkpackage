from django.conf import settings
from django.core.management.base import BaseCommand

import os
import unicodedata, re

import logging
logger = logging.getLogger(__name__)

from ims.models import User, Client, ClientUser


class Command(BaseCommand):

    def handle(self, *args, **options):
        user = User.objects.get(email=settings.CLIENTACCESS_EMAIL)

        for client in Client.objects.all():
            client_user, created = ClientUser.objects.get_or_create(user=user, client=client)
            if created:
                print('Added {0}'.format(client))
