from django.conf import settings
from django.core.management.base import BaseCommand

import os

import logging
logger = logging.getLogger(__name__)

from ims.models import Product, Location


class Command(BaseCommand):

    def handle(self, *args, **options):
        for product in Product.objects.all():
            if product.is_active == -1:
                product.is_active = 0
                product.is_deleted = 1
            try:
                print product.location
            except Location.DoesNotExist:
                product.location = None
            product.save()
