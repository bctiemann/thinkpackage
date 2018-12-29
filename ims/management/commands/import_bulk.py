from django.conf import settings
from django.core.management.base import BaseCommand

import os
import unicodedata, re
import csv
import datetime

import logging
logger = logging.getLogger(__name__)

from ims.models import Client, Location, BulkOrder, BulkOrderItem, Shipment, Product, Transaction


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--ftp_path', dest='ftp_path',)

    def handle(self, *args, **options):

        ftp_path = options.get('ftp_path', None)
        if not ftp_path:
            print('Missing --ftp_path <path>')
            raise SystemExit

        for customer_dir in os.listdir(ftp_path):
            customer_dir_absolute = os.path.join(ftp_path, customer_dir)
            if os.path.isdir(customer_dir_absolute) and re.match(r'^[0-9]+$', customer_dir):
                try:
                    client = Client.objects.get(id=customer_dir)
                except Client.DoesNotExist:
                    print('{0}: No customer found; skipping'.format(customer_dir,))
                    continue
                print('{0}: {1}'.format(customer_dir, client))

                for filename in os.listdir(customer_dir_absolute):
                    if filename.endswith('.txt'):
                        filename_parts = filename.split('_')
                        order_date = datetime.datetime.strptime(filename_parts[1], '%Y%m%d')

                        filename_absolute = os.path.join(customer_dir_absolute, filename)
                        with open(filename_absolute) as csv_file:
                            csv_reader = csv.reader(csv_file, delimiter=',')
                            line_count = 0
                            bulk_order_id = None
                            for row in csv_reader:
                                if not row:
                                    continue

                                if row[0] == 'H':

                                    try:
                                        location = Location.objects.get(client=client, name=row[5])
                                    except Location.DoesNotExist:
                                        print('Location {0} not found.'.format(row[5]))
                                        continue
                                    print location

                                    delivery_date = datetime.datetime.strptime(row[3], '%Y%m%d')

                                    bulk_order = BulkOrder.objects.create(
                                        filename = filename,
                                        date_ordered = order_date,
                                        purchase_order = row[2],
                                        date_delivery = delivery_date,
                                        account_number = row[1],
                                        message = row[4],
                                        location_address_1 = row[6],
                                        location_address_2 = row[7],
                                        location_city = row[8],
                                        location_state = row[9],
                                        location_zip = row[10],
                                        client = client,
                                        location = location,
                                    )
                                    print bulk_order

                                elif row[0] == 'D':

                                    bulk_order_item = BulkOrderItem.objects.create(
                                        bulk_order = bulk_order,
                                        item_number = row[3],
                                        quantity = row[4],
                                        package_type = row[5],
                                        split_flag = row[6],
                                        product_name = row[7],
                                        bid_price = row[8],
                                    )
                                    print bulk_order_item

                        print('Imported file {0}'.format(filename))
#                        os.rename(filename_absolute, os.path.join(ftp_path, 'archive', customer_dir, filename))

                        shipment = Shipment.objects.create(
                            client = client,
                            date_shipped = None,
                            purchase_order_number = bulk_order.purchase_order,
                            accounting_status = 0,
                            shipper_instructions = bulk_order.message,
                            location = location,
                        )

                        bulk_order.shipment = shipment
                        bulk_order.save()

                        for bulk_order_item in bulk_order.bulkorderitem_set.all():

                            try:
                                product = Product.objects.get(client=client, item_number=bulk_order_item.item_number, is_active=True)
                            except Product.DoesNotExist:
                                print('Product matching itemnum {0} not found.'.format(bulk_order_item.item_number))
                                continue

                            transaction = Transaction.objects.create(
                                product = product,
                                cases = bulk_order_item.quantity,
                                is_outbound = True,
                                shipment = shipment,
                                client = client,
                            )

                        print('Created shipment {0}'.format(shipment.id))
