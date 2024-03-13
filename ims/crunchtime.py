import csv
from datetime import date, datetime
from typing import List

import logging
import paramiko
import os
import re
from dataclasses import dataclass

from django.conf import settings

from ims.models import Location, Client, Product, Shipment, User
from ims.shipment import RequestedProduct, add_products_to_shipment, send_shipment_notifications

logger = logging.getLogger("crunchtime")


@dataclass
class ProductOrder:
    product: Product
    quantity: int
    split_flag: bool


@dataclass
class PurchaseOrder:
    client: Client
    location: Location
    po_number: str
    delivery_date: date
    product_orders: List[ProductOrder]


class PurchaseOrderException(Exception):
    pass


class NoPrimaryUserException(Exception):
    pass


class CrunchtimeService:
    host = None
    username = None
    password = None
    port = None
    config = None
    ssh_client = None
    local_file_dir = "/tmp"
    po_dir = "po"
    inbound_dir = "inbound"

    PO_HEADER_FIELDS = [
        "line_type_indicator",
        "vendor_location_id",
        "purchase_order_number",
        "delivery_date",
        "special_instructions",
    ]
    PO_DETAIL_FIELDS = [
        "line_type_indicator",
        "vendor_location_id",
        "purchase_order_number",
        "vendor_product_number",
        "order_quantity",
        "vendor_unit_of_measure",
        "split_flag",
    ]
    LINE_TYPE_HEADER = "H"
    LINE_TYPE_DETAIL = "D"

    # PO filename format: CTPO_20240305_022301_VO1235.txt
    RE_PO_FILENAME = re.compile(r"^CTPO_[0-9]{8}_[0-9]{6}_VO[0-9]+\.txt$")

    def __init__(self, config):
        self.config = settings.CRUNCHTIME_SFTP.get(config)
        self.host = self.config['HOST']
        self.port = self.config['PORT']
        self.username = self.config['USER']
        self.password = self.config['PASSWORD']
        self.po_dir = self.config.get('PO_DIR') or self.po_dir
        self.inbound_dir = self.config.get('INBOUND_DIR') or self.inbound_dir
        self.local_file_dir = self.config.get('LOCAL_FILE_DIR') or self.local_file_dir
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        self.ssh_client.connect(self.host, self.port, username=self.username, password=self.password)

    def list_files(self, path=''):
        self.connect()
        ftp = self.ssh_client.open_sftp()
        files = ftp.listdir(path=path)
        ftp.close()
        return files

    def get_new_purchase_orders(self):
        new_purchase_orders = []
        po_files = self.list_files(self.po_dir)
        inbound_files = self.list_files(self.inbound_dir)
        for filename in po_files:
            if re.match(self.RE_PO_FILENAME, filename):
                purchase_order_number = self.get_purchase_order_number_from_filename(filename)
                confirmation_file = self.get_confirmation_filename(purchase_order_number)
                if confirmation_file not in inbound_files:
                    new_purchase_orders.append(filename)
        return new_purchase_orders

    def get_purchase_order_number_from_filename(self, filename):
        base_filename = ".".join(filename.split(".")[0:-1])
        return base_filename.split("_")[-1].replace("VO", "")

    # Confirmation filename format: 011_VO1235.txt
    def get_confirmation_filename(self, purchase_order_number):
        return f"011-VO{purchase_order_number}.txt"

    def get_local_file_path(self, filename):
        return os.path.join(self.local_file_dir, filename)

    def get_file(self, file_path):
        self.connect()
        ftp = self.ssh_client.open_sftp()
        filename = os.path.split(file_path)[-1]
        local_file_path = self.get_local_file_path(filename)
        try:
            ftp.get(file_path, local_file_path)
        except OSError as e:
            print(f"File {file_path} not available: {e}")
            raise e
        finally:
            ftp.close()
        self.ssh_client.close()
        return local_file_path

    def put_file(self, filename, remote_dir=''):
        self.connect()
        ftp = self.ssh_client.open_sftp()
        local_file_path = self.get_local_file_path(filename)
        remote_path = os.path.join(remote_dir, filename)
        result = ftp.put(local_file_path, remote_path)
        ftp.close()
        return result

    def get_purchase_order_data(self, filename):
        header_data = {}
        detail_data = []
        po_filename = os.path.join(self.po_dir, filename)
        try:
            po_file = self.get_file(po_filename)
        except Exception as e:
            raise e
        with open(po_file, "r") as f:
            csv_file = csv.reader(f)
            for line in csv_file:
                if len(line) == 0:
                    continue
                if line[0] == self.LINE_TYPE_HEADER:
                    header_data = {h[0]: h[1] for h in zip(self.PO_HEADER_FIELDS, line)}
                elif line[0] == self.LINE_TYPE_DETAIL:
                    detail_data.append({d[0]: d[1] for d in zip(self.PO_DETAIL_FIELDS, line)})
        location_id = header_data["vendor_location_id"]
        purchase_order_number = header_data["purchase_order_number"]
        try:
            location = Location.objects.get(pk=location_id)
        except Location.DoesNotExist:
            error_message = f"{filename}: Location {location_id} does not exist. File will not be processed."
            logger.error(error_message)
            raise PurchaseOrderException(error_message)
        delivery_date = datetime.strptime(header_data["delivery_date"], "%Y%m%d")
        po_data = PurchaseOrder(
            client=location.client,
            location=location,
            po_number=purchase_order_number,
            delivery_date=delivery_date,
            product_orders=[],
        )
        for detail in detail_data:
            item_number = detail["vendor_product_number"]
            try:
                product = Product.objects.get(
                    item_number=item_number, is_active=True, is_deleted=False, client=location.client
                )
            except Product.DoesNotExist:
                logger.warning(f"{filename}: Product {item_number} does not exist. Skipping.")
                continue
            split_flag = detail["split_flag"].lower() == "Y"
            product_order = ProductOrder(
                product=product,
                quantity=int(detail["order_quantity"]),
                split_flag=split_flag,
            )
            po_data.product_orders.append(product_order)

        return po_data

    def get_user(self, purchase_order: PurchaseOrder) -> User:
        primary_client_user = purchase_order.client.clientuser_set.filter(is_primary=True).first()
        if not primary_client_user:
            raise NoPrimaryUserException(f"No primary ClientUser for client {purchase_order.client}")
        return primary_client_user.user

    def create_shipment(self, purchase_order: PurchaseOrder) -> Shipment:
        user = self.get_user(purchase_order)

        shipment = Shipment.objects.create(
            client=purchase_order.client,
            user=user,
            status=Shipment.Status.PENDING,
            location=purchase_order.location,
            purchase_order_number=purchase_order.po_number,
            purchase_order_deadline=purchase_order.delivery_date
        )
        requested_products = []
        for product_order in purchase_order.product_orders:
            requested_products.append(RequestedProduct(product=product_order.product, cases=product_order.quantity))
        add_products_to_shipment(
            shipment=shipment,
            requested_products=requested_products,
            client=purchase_order.client,
        )
        send_shipment_notifications(shipment, client_email=user.email)
        return shipment

    def confirm_receipt(self, purchase_order: PurchaseOrder, shipment: Shipment):
        filename = self.get_confirmation_filename(purchase_order.po_number)
        local_file_path = self.get_local_file_path(filename)

        confirmation_data = [
            "H",
            str(purchase_order.location.id),
            purchase_order.po_number,
            datetime.now().strftime("%Y%m%d%H%M%S"),
            str(shipment.id),
        ]
        confirmation_content = "|".join(confirmation_data)

        with open(local_file_path, 'w') as f:
            f.write(confirmation_content)
        self.put_file(filename, self.inbound_dir)

    def process_new_purchase_orders(self):
        new_purchase_orders = self.get_new_purchase_orders()
        logger.info(new_purchase_orders)
        for po_file in new_purchase_orders:
            try:
                purchase_order = self.get_purchase_order_data(po_file)
            except PurchaseOrderException as e:
                print(e)
                continue
            print(purchase_order)
            logger.info(purchase_order)
            shipment = self.create_shipment(purchase_order)
            self.confirm_receipt(purchase_order, shipment)
