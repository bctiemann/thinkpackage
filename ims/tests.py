from django.test import TestCase

from ims.models import Client, User, Shipment, Transaction, Receivable

class ShipmentTestCase(TestCase):
    fixtures = ['ShipperAddress']

    def setUp(self):
        self.client = Client.objects.create(company_name="Client 1")

    def test_shipment_created_as_pending(self):
        shipment = Shipment.objects.create(client=self.client)
        self.assertEqual(shipment.is_pending, True)