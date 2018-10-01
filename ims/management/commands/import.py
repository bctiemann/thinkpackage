from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import six, timezone

import os
import unicodedata, re
import MySQLdb

import logging
logger = logging.getLogger(__name__)

from ims import models as ims_models


class Command(BaseCommand):

    enabled = {
        'do_clients': True,
    }

    def add_arguments(self, parser):
        parser.add_argument('--key', dest='key',)

    def handle(self, *args, **options):
        legacy_db = settings.DATABASES['legacy']
        db = MySQLdb.connect(passwd=legacy_db['PASSWORD'], db=legacy_db['NAME'], host=legacy_db['HOST'], user=legacy_db['USER'], charset=legacy_db['OPTIONS']['charset'])
        c = db.cursor(MySQLdb.cursors.DictCursor)

        if 'do_clients' in self.enabled:
            c.execute("""SELECT * FROM customers""")
            for old in c.fetchall():
                print old['coname']
                new = ims_models.Client.objects.create(
                    id = old['customerid'],
                    email = old['email'] or '',
                    created_on = old['createdon'],
                    is_preferred = old['preferred'],
                    is_active = old['enabled'],
                    notes = old['notes'] or '',
                    company_name = old['coname'],
                    has_warehousing = old['warehousing'],
                )
            c.execute("""SELECT * FROM customers""")
            for old in c.fetchall():
                if old['parent']:
                    new = ims_models.Client.objects.get(id=old['customerid'])
                    new.parent_id = old['parent']
                    new.save()

