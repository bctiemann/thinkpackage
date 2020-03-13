from decimal import Decimal

from django.test import TestCase, Client as TestClient

from ims.models import Client, Location, User, Product, Shipment, Transaction, Receivable

class ShipmentTestCase(TestCase):
    fixtures = ['ShipperAddress']

    def setUp(self):
        self.client = Client.objects.create(company_name="Client 1")

    def test_shipment_created_as_pending(self):
        shipment = Shipment.objects.create(client=self.client)
        self.assertEqual(shipment.is_pending, True)


class ProductTestCase(TestCase):
    fixtures = ['User']

    def setUp(self):
        self.test_client = TestClient()
        self.test_client.login(username='test@example.com', password='test123')
        self.client = Client.objects.create(company_name="Client 1")
        self.product = Product.objects.create(
            client=self.client,
            name='Test Product',
            unit_price=0,
            gross_weight=0,
            length=0,
            height=0,
            width=0,
        )

    def test_update_product(self):
        self.assertEqual(self.product.name, 'Test Product')
        payload = {
            'client': self.client.id,
            'item_number': '00001',
            'location': '',
            'client_tag': 'Client Tag',
            'name': 'Updated Name',
            'packing': 500,
            'cases_inventory': 35,
            'PO': '',
            'contracted_quantity': 100000,
            'unit_price': '1.01',
            'gross_weight': 0,
            'length': 0,
            'width': 0,
            'height': 0,
            'is_domestic': 1,
            'accounting_prepay_type': 1,
        }
        response = self.test_client.post(f'/mgmt/product/{self.product.id}/', payload)
        self.assertEqual(response.status_code, 302)
        updated_product = Product.objects.get(pk=self.product.id)
        self.assertEqual(updated_product.unit_price, Decimal('1.01'))