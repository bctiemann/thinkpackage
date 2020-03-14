from decimal import Decimal
import json

from django.test import TestCase, Client as TestClient
from django.urls import reverse, reverse_lazy

from ims.models import Client, Location, User, Product, Shipment, Transaction, Receivable


json_headers = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


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
        self.payload = {
            'client': self.client.id,
            'item_number': '00001',
            'location': '',
            'client_tag': 'Client Tag',
            'name': 'Updated Name',
            'packing': 500,
            'cases_inventory': 35,
            'PO': '',
            'contracted_quantity': 100000,
            'unit_price': 0,
            'gross_weight': 0,
            'length': 0,
            'width': 0,
            'height': 0,
            'is_domestic': 1,
            'accounting_prepay_type': 1,
        }

    def test_create_product(self):
        payload = self.payload
        url = reverse('mgmt:product-add', kwargs={'client_id': self.client.id})

        payload['unit_price'] = '1.01'
        response = self.test_client.post(url, payload, **json_headers)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        new_product_id = result['pk']
        new_product = Product.objects.get(pk=new_product_id)
        self.assertEqual(new_product.unit_price, Decimal('1.01'))

    def test_unit_price(self):
        payload = self.payload
        url = reverse('mgmt:product-update', kwargs={'product_id': self.product.id})

        payload['unit_price'] = '1.01'
        response = self.test_client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        updated_product = Product.objects.get(pk=self.product.id)
        self.assertEqual(updated_product.unit_price, Decimal('1.01'))

        payload['unit_price'] = 'abc'
        response = self.test_client.post(url, payload)
        self.assertEqual(response.status_code, 200)
        updated_product = Product.objects.get(pk=self.product.id)
        self.assertEqual(updated_product.unit_price, Decimal('1.01'))

        del payload['unit_price']
        response = self.test_client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        updated_product = Product.objects.get(pk=self.product.id)
        self.assertEqual(updated_product.unit_price, Decimal('0'))

        updated_product.unit_price = Decimal('1.01')
        updated_product.save()

        payload['unit_price'] = ''
        response = self.test_client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        updated_product = Product.objects.get(pk=self.product.id)
        self.assertEqual(updated_product.unit_price, Decimal('0'))

    def test_gross_weight(self):
        payload = self.payload
        url = reverse('mgmt:product-update', kwargs={'product_id': self.product.id})

        payload['gross_weight'] = '1.01'
        response = self.test_client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        updated_product = Product.objects.get(pk=self.product.id)
        self.assertEqual(updated_product.gross_weight, Decimal('1.01'))
