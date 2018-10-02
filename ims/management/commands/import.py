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
#        'do_clients': True,
#        'do_custcontacts': True,
        'do_locations': True,
#        'do_products': True,
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

        if 'do_custcontacts' in self.enabled:
            c.execute("""SELECT * FROM custcontacts""")
            for old in c.fetchall():
                print old['email']
                new  = ims_models.CustContact.objects.create(
                    id = old['custcontactid'],
                    client_id = old['customerid'],
                    email = old['email'],
                    password = old['pass'],
                    first_name = old['fname'],
                    last_name = old['lname'],
                    title = old['title'] or '',
                    phone_number = old['tel'] or '',
                    phone_extension = old['telext'] or '',
                    fax_number = old['fax'] or '',
                    mobile_number = old['mobile'] or '',
                    is_primary = old['isprimary'],
                    is_active = old['enabled'],
                    last_login = old['lastlogin'],
                    notes = old['notes'] or '',
                )

        if 'do_products' in self.enabled:
            prepay = {}
            for choice in ims_models.Product.PREPAY_CHOICES:
                prepay[choice[0]] = choice[1]

            c.execute("""SELECT * FROM products""")
            for old in c.fetchall():
                print old['pname']
                new  = ims_models.Product.objects.create(
                    id = old['productid'],
                    client_id = old['client'],
                    product_id = old['PRID'],
                    date_created = old['createdon'],
                    packing = old['packing'],
                    cases_inventory = old['remain'],
                    units_inventory = old['totalq'],
                    unit_price = old['unitprice'],
                    gross_weight = old['GW'],
                    is_domestic = old['prodtype'],
                    name = old['pname'],
                    client_tag = old['ctag'],
                    contracted_quantity = old['contqty'],
                    is_active = old['active'],
                    length = old['length'],
                    width = old['width'],
                    height = old['height'],
                    item_number = old['itemnum'],
                    location_id = old['locationid'],
                    account_prepay_type = old['account']
                )
