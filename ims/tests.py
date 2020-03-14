from decimal import Decimal
import json

from django.test import TestCase, Client as TestClient
from django.urls import reverse, reverse_lazy

from ims.models import Client, Location, User, Product, Shipment, Transaction, Receivable


ajax_headers = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


class ShipmentTestCase(TestCase):
    fixtures = ['ShipperAddress']

    def setUp(self):
        self.client = Client.objects.create(company_name="Client 1")

    def test_shipment_created_as_pending(self):
        shipment = Shipment.objects.create(client=self.client)
        self.assertEqual(shipment.is_pending, True)
