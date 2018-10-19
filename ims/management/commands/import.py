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
#        'do_warehouseusers': True,
#        'do_locations': True,
#        'do_products': True,
#        'do_shipments': True,
#        'do_receivables': True,
#        'do_transactions': True,
#        'do_pallets': True,
#        'do_palletcontents': True,
#        'do_shipmentdocs': True,
        'do_actionlogs': True,
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
                    is_preferred = old['preferred'],
                    is_active = old['enabled'],
                    notes = old['notes'] or '',
                    company_name = old['coname'],
                    has_warehousing = old['warehousing'],
                )
                new.created_on = old['createdon']
                new.save()
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
                    pic_first_name = old['picfname'] or '',
                    mobile_number = old['cell'] or '',
                    two_factor_type = old['twofac'],
                    is_active = old['enable'],
                )
                new.date_created = old['stamp']
                new.save()
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
                    last_login = old['lastlogin'],
                    login_count = old['logintimes'],
                    is_active = old['enable'],
                    role = old['role'],
                )
                new.date_created = old['createdon']
                new.save()
            c.execute("""SELECT * FROM wuser WHERE createdbyadminid IS NOT NULL""")
            for old in c.fetchall():
                new = ims_models.WarehouseUser.objects.get(id=old['wuserid'])
                try:
                    creator = ims_models.AdminUser.objects.get(pk=old['createdbyadminid'])
                except ims_models.DoesNotExist:
                    creator = None
                new.created_by = creator
                new.save()

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
                    packing = old['packing'],
                    cases_inventory = old['remain'],
                    units_inventory_old = old['totalq'],
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
                new.date_created = old['createdon']
                new.save()

        if 'do_shipments' in self.enabled:
            c.execute("""SELECT * FROM shipments""")
            for old in c.fetchall():
                print old['shipmentid']
                try:
                    client = ims_models.Client.objects.get(pk=old['customerid'])
                except ims_models.Client.DoesNotExist:
                    client = None
                try:
                    location = ims_models.Location.objects.get(pk=old['locationid'])
                except ims_models.Location.DoesNotExist:
                    location = None
                new  = ims_models.Shipment.objects.create(
                    id = old['shipmentid'],
                    client = client,
                    date_shipped = old['shippedon'],
                    status = old['status'],
                    carrier = old['carrier'] or '',
                    tracking = old['tracking'] or '',
                    purchase_order = old['PO'] or '',
                    shipment_order = old['SO'] or '',
                    location = location,
                    third_party = old['3rdparty'] or '',
                    third_party_address = old['3rdpartyaddress'] or '',
                    third_party_phone_number = old['3rdpartyphone'] or '',
                    third_party_per = old['3rdpartyper'] or '',
                    third_party_received = old['3rdpartyrecvd'] or '',
                    third_party_charges_advanced = old['3rdpartychgadvanced'] or '',
                    pro_number = old['pro'] or '',
                    purchase_order_number = old['loadnum'] or '',
                    shipper_instructions = old['shipperinstructions'] or '',
                    consignee_instructions = old['consigneeinstructions'] or '',
                    shipper_address_id = old['shipperaddress'],
                    inside_delivery = old['insidedelivery'] or False,
                    liftgate_required = old['liftgate'] or False,
                    appointment_required = old['appointment'] or False,
                    sort_segregation = old['sortseg'] or False,
                    shipment_class = old['class'] or '',
                    pallet_count = old['numpallets'],
                    accounting_status = old['acctstatus'],
                    invoice_number = old['invoice'],
                    delivery_charge = old['deliverycharge'],
                )
                new.date_created = old['createdon']
                new.save()

        if 'do_receivables' in self.enabled:
            c.execute("""SELECT * FROM receivables""")
            for old in c.fetchall():
                print old['receivableid']
                try:
                    client = ims_models.Client.objects.get(pk=old['customerid'])
                except ims_models.Client.DoesNotExist:
                    client = None
                try:
                    product = ims_models.Product.objects.get(pk=old['productid'])
                except ims_models.Product.DoesNotExist:
                    product = None
                new  = ims_models.Receivable.objects.create(
                    id = old['receivableid'],
                    client = client,
                    purchase_order = old['PO'] or '',
                    shipment_order = old['SO'] or '',
                    product = product,
                    cases = old['cases'],
                )
                new.date_created = old['createdon']
                new.save()

        if 'do_transactions' in self.enabled:
            c.execute("""SELECT * FROM transactions""")
            for old in c.fetchall():
                print old['transactionid']
                try:
                    product = ims_models.Product.objects.get(pk=old['productid'])
                except ims_models.Product.DoesNotExist:
                    product = None
                try:
                    shipment = ims_models.Shipment.objects.get(pk=old['shipmentid'])
                except ims_models.Shipment.DoesNotExist:
                    shipment = None
                try:
                    client = ims_models.Client.objects.get(pk=old['customerid'])
                except ims_models.Client.DoesNotExist:
                    client = None
                try:
                    receivable = ims_models.Receivable.objects.get(pk=old['receivableid'])
                except ims_models.Receivable.DoesNotExist:
                    receivable = None
                try:
                    transfer_client = ims_models.Client.objects.get(pk=old['transfercustomerid'])
                except ims_models.Client.DoesNotExist:
                    transfer_client = None
                try:
                    transfer_product = ims_models.Product.objects.get(pk=old['transferproductid'])
                except ims_models.Product.DoesNotExist:
                    transfer_product = None
                new  = ims_models.Transaction.objects.create(
                    id = old['transactionid'],
                    product = product,
                    quantity = old['qty'],
#                    quantity_remaining = old['qtyremain'],
                    cases_remaining = old['qtyremain'] / product.packing if product.packing else 0,
                    is_outbound = old['direction'],
                    shipment = shipment,
                    client = client,
                    cases = old['cases'],
                    shipment_order = old['SO'] or '',
                    receivable = receivable,
                    transfer_client = transfer_client,
                    transfer_product = transfer_product,
                )
                new.date_created = old['stamp']
                new.save()

        if 'do_pallets' in self.enabled:
            c.execute("""SELECT * FROM pallets""")
            for old in c.fetchall():
                print old['palletid']
                try:
                    shipment = ims_models.Shipment.objects.get(pk=old['shipmentid'])
                except ims_models.Shipment.DoesNotExist:
                    shipment = None
                try:
                    client = ims_models.Client.objects.get(pk=old['customerid'])
                except ims_models.Client.DoesNotExist:
                    client = None
                new  = ims_models.Pallet.objects.create(
                    id = old['palletid'],
                    pallet_id = old['PID'] or '',
                    shipment = shipment,
                    client = client,
                )
                new.date_created = old['createdon']
                new.save()

        if 'do_palletcontents' in self.enabled:
            c.execute("""SELECT * FROM onpallet""")
            for old in c.fetchall():
                print old['palletid'], old['productid']
                try:
                    pallet = ims_models.Pallet.objects.get(pk=old['palletid'])
                except ims_models.Pallet.DoesNotExist:
                    pallet = None
                try:
                    product = ims_models.Product.objects.get(pk=old['productid'])
                except ims_models.Product.DoesNotExist:
                    product = None
                new  = ims_models.PalletContents.objects.create(
                    id = old['onpalletid'],
                    pallet = pallet,
                    product = product,
                    cases = old['qty'],
                )

        if 'do_shipmentdocs' in self.enabled:
            c.execute("""SELECT * FROM shipmentdocs""")
            for old in c.fetchall():
                print old['docid']
                try:
                    shipment = ims_models.Shipment.objects.get(pk=old['shipmentid'])
                except ims_models.Shipment.DoesNotExist:
                    shipment = None
                new  = ims_models.ShipmentDoc.objects.create(
                    id = old['docid'],
                    shipment = shipment,
                    uuid = old['uuid'],
                    file = '{0}/{1}.{2}'.format(old['uuid'], old['basename'], old['ext']),
                    basename = old['basename'] or '',
                    ext = old['ext'] or '',
                    size = old['size'],
                    content_type = old['mimetype'],
                )
                new.date_created = old['stamp']
                new.save()

        if 'do_actionlogs' in self.enabled:
            c.execute("""SELECT * FROM actionlogs""")
            for old in c.fetchall():
                print old['log_message']
                app = ''
                try:
                    admin_user = ims_models.AdminUser.objects.get(pk=old['adminid'])
                    app = 'mgmt'
                except ims_models.AdminUser.DoesNotExist:
                    admin_user = None
                try:
                    warehouse_user = ims_models.WarehouseUser.objects.get(pk=old['wuserid'])
                except ims_models.WarehouseUser.DoesNotExist:
                    warehouse_user = None
                    app = 'warehouse'
                try:
                    client = ims_models.Client.objects.get(pk=old['customerid'])
                except ims_models.Client.DoesNotExist:
                    client = None
                try:
                    product = ims_models.Product.objects.get(pk=old['productid'])
                except ims_models.Product.DoesNotExist:
                    product = None
                new = ims_models.ActionLog.objects.create(
                    admin_user = admin_user,
                    warehouse_user = warehouse_user,
                    client = client,
                    product = product,
                    log_message = old['log_message'],
                    app = app,
                )
                new.date_created = old['stamp']
                new.save()
