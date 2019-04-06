from django.conf import settings
from django.core.management.base import BaseCommand

import os

import logging
logger = logging.getLogger(__name__)

from ims.models import Product, Location, Receivable, Transaction, Shipment


class Command(BaseCommand):

    def handle(self, *args, **options):
#        self.clean_products()
        self.clean_transactions()

    def clean_products(self):
        for product in Product.objects.all():
            if product.is_active == -1:
                product.is_active = 0
                product.is_deleted = 1
            try:
                print(product.location)
            except Location.DoesNotExist:
                product.location = None
            product.save()

    def clean_transactions(self):
        for transaction in Transaction.objects.all():
            print(transaction)
            try:
                print('Shipment: {0}'.format(transaction.shipment))
            except Shipment.DoesNotExist:
                print('Nulling shipment')
                transaction.shipment = None
            try:
                print('Receivable: {0}'.format(transaction.receivable))
            except Receivable.DoesNotExist:
                print('Nulling receivable')
                transaction.receivable = None
            transaction.save()
