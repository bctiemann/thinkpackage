import logging
from dataclasses import dataclass
from typing import List

from django.conf import settings

from ims.models import Shipment, Product, Transaction
from ims.tasks import email_purchase_order, email_delivery_request, sps_submit_shipment

logger = logging.getLogger(__name__)


@dataclass
class RequestedProduct:
    product: Product
    cases: int


def create_or_update_shipment():
    pass


def add_products_to_shipment(shipment: Shipment, requested_products: List[RequestedProduct], client=None):
    # Create new transactions for each requested product
    total_cases = 0
    for requested_product in requested_products:

        if requested_product.cases > requested_product.product.cases_available:
            logger.warning(f"Requested {requested_product.cases} cases of product {requested_product.product}, {requested_product.product.cases_available} available. Skipping.")
            continue
        if not requested_product.product.is_active or requested_product.product.is_deleted:
            logger.warning(f"Requested product {requested_product.product} is inactive or deleted. Skipping.")
            continue

        transaction = Transaction(
            product=requested_product.product,
            is_outbound=True,
            shipment=shipment,
            client=client,
            cases=requested_product.cases,
        )
        transaction.save()
        logger.info(f'{transaction.cases}\t{transaction.product}')
        total_cases += requested_product.cases

    return total_cases


def send_shipment_notifications(shipment: Shipment, shipment_updated=False, client_email=None):
    # Send a notification email to the configured delivery admin
    email_delivery_request.delay(
        shipment_id=shipment.id, shipment_updated=shipment_updated, client_email=client_email
    )
    logger.info('Launched email_delivery_request task')

    # Generate PO PDF and email to PO address
    email_purchase_order.delay(shipment_id=shipment.id)
    logger.info('Launched email_purchase_order task')

    # Submit shipment payload to SPS
    if settings.SPS_ENABLE and settings.SPS_SUBMIT_ON_CREATE:
        sps_submit_shipment.delay(shipment.id)
        logger.info('Launched sps_submit_shipment task')
