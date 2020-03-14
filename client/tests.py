from decimal import Decimal
import json

from django.test import TestCase, Client as TestClient
from django.urls import reverse, reverse_lazy

from ims.models import Client, ClientUser, Location, User, Product, Shipment, Transaction, Receivable
from ims.tests import ajax_headers


class AuthTestCase(TestCase):
    fixtures = ['User']

    def setUp(self):
        self.test_client = TestClient()
        self.client = Client.objects.create(company_name="Client 1")
        self.client.save()
        self.client_user = User.objects.get(email='client_user@example.com')
        ClientUser.objects.create(
            client=self.client,
            user=self.client_user,
            title='Master and Commander',
        )

    def test_admin_access(self):
        url = reverse('client:home')

        self.test_client.login(username='admin_user@example.com', password='test123')
        response = self.test_client.get(url)
        print(response.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

    def test_no_warehouse_access(self):
        url = reverse('client:home')

        self.test_client.login(username='warehouse_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_no_accounting_access(self):
        url = reverse('client:home')

        self.test_client.login(username='accounting_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_client_access(self):
        url = reverse('client:home')

        self.test_client.login(username='client_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

    def test_invalid_login(self):
        url = reverse('client:home')

        self.test_client.login(username='admin_user@example.com', password='bad-password')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:login'))

    def test_inactive_user(self):
        url = reverse('client:home')

        self.test_client.login(username='inactive_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:login'))


