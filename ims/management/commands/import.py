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
#        'do_adminusers': True,
        'do_warehouseusers': True,
#        'do_locations': True,
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
            c.execute("""SELECT * FROM customers WHERE parent IS NOT NULL""")
            for old in c.fetchall():
                new = ims_models.Client.objects.get(id=old['customerid'])
                new.parent_id = old['parent']
                new.save()

        if 'do_custcontacts' in self.enabled:
            c.execute("""SELECT * FROM custcontacts""")
            for old in c.fetchall():
                print old['email']
                new = ims_models.CustContact.objects.create(
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

        if 'do_adminusers' in self.enabled:
            c.execute("""SELECT * FROM admin""")
            for old in c.fetchall():
                print old['fullname'].encode('utf8')
                new = ims_models.AdminUser.objects.create(
                    id = old['adminid'],
                    username = old['user'],
                    password = old['pass'],
                    is_authority = old['authority'],
                    is_founder = old['founder'],
                    full_name = old['fullname'],
                    email = old['email'] or '',
                    about = old['about'] or '',
                    access_level = old['acclev'],
                    is_sleeping = old['sleeping'] or False,
                    date_created = old['stamp'],
                    pic_first_name = old['picfname'] or '',
                    mobile_number = old['cell'] or '',
                    two_factor_type = old['twofac'],
                    is_active = old['enable'],
                )
            c.execute("""SELECT * FROM admin WHERE createdbyadminid IS NOT NULL""")
            for old in c.fetchall():
                new = ims_models.AdminUser.objects.get(id=old['adminid'])
                try:
                    creator = ims_models.AdminUser.objects.get(pk=old['createdbyadminid'])
                except ims_models.DoesNotExist:
                    creator = None
                new.created_by = creator
                new.save()

        if 'do_warehouseusers' in self.enabled:
            c.execute("""SELECT * FROM wuser""")
            for old in c.fetchall():
                print old['fullname'].encode('utf8')
                new = ims_models.WarehouseUser.objects.create(
                    id = old['wuserid'],
                    username = old['user'],
                    password = old['pass'],
                    full_name = old['fullname'] or '',
                    email = old['email'],
                    about = old['about'] or '',
                    date_created = old['createdon'],
                    last_login = old['lastlogin'],
                    login_count = old['logintimes'],
                    is_active = old['enable'],
                    role = old['role'],
                )
            c.execute("""SELECT * FROM wuser WHERE createdbyadminid IS NOT NULL""")
            for old in c.fetchall():
                new = ims_models.WarehouseUser.objects.get(id=old['wuserid'])
                try:
                    creator = ims_models.AdminUser.objects.get(pk=old['createdbyadminid'])
                except ims_models.DoesNotExist:
                    creator = None
                new.created_by = creator
                new.save()

#    id = models.AutoField(primary_key=True, db_column='wuserid')
#    username = models.CharField(max_length=100, blank=True, db_column='user')
#    password = models.CharField(max_length=255, blank=True, db_column='pass')
#    created_by = models.ForeignKey('AdminUser', null=True, blank=True, db_column='createdbyadminid')
#    full_name = models.CharField(max_length=150, blank=True, db_column='fullname')
#    email = models.EmailField(max_length=192, blank=True)
#    about = models.TextField(blank=True)
#    date_created = models.DateTimeField(auto_now_add=True, db_column='createdon')
#    last_login = models.DateTimeField(null=True, db_column='lastlogin')
#    login_count = models.IntegerField(default=0, db_column='logintimes')
#    is_active = models.BooleanField(default=True, db_column='enable')
#    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

        if 'do_locations' in self.enabled:
            c.execute("""SELECT * FROM locations""")
            for old in c.fetchall():
                print old['name'].encode('utf8')
                new = ims_models.Location.objects.create(
                    id = old['locationid'],
                    client_id = old['customerid'],
                    name = old['name'],
                    phone_number = old['tel'] or '',
                    phone_extension = old['telext'] or '',
                    fax_number = old['fax'] or '',
                    address = old['addr'] or '',
                    address_2 = old['addr2'] or '',
                    city = old['city'] or '',
                    state = old['state'] or '',
                    zip = old['zip'] or '',
                    country = old['country'] or '',
                    non_us_state = old['ostate'] or '',
                    customer_contact_id = old['custcontactid'] or None,
                    notes = old['notes'] or '',
                    receiving_hours = old['recvhours'] or '',
                )

        if 'do_products' in self.enabled:
            c.execute("""SELECT * FROM products""")
            for old in c.fetchall():
                print old['pname'].encode('utf8')
                try:
                    location = ims_models.Location.objects.get(pk=old['locationid'])
                except ims_models.Location.DoesNotExist:
                    location = None
                new  = ims_models.Product.objects.create(
                    id = old['productid'],
                    client_id = old['customerid'] or None,
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
                    is_active = old['active'] if old['active'] >= 0 else False,
                    is_deleted = True if old['active'] == -1 else False,
                    length = old['length'],
                    width = old['width'],
                    height = old['height'],
                    item_number = old['itemnum'],
                    location = location,
                    account_prepay_type = old['account']
                )

