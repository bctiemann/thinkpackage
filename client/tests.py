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
        self.child_client = Client.objects.create(company_name="Child Client", parent=self.client)
        self.other_client = Client.objects.create(company_name="Client 2")
        self.client_user = User.objects.get(email='client_user@example.com')
        self.admin_user = User.objects.get(email='admin_user@example.com')
        ClientUser.objects.create(
            client=self.client,
            user=self.client_user,
            title='Master and Commander',
        )

    # Admin user (with no client linkages) has access to client site
    def test_admin_access(self):
        url = reverse('client:home')

        self.test_client.login(username='admin_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

    # Admin user (with a client linkage) has access to client site
    def test_admin_access_with_client_link(self):
        url = reverse('client:home')

        ClientUser.objects.create(
            client=self.client,
            user=self.admin_user,
            title='BOFH',
        )
        self.test_client.login(username='admin_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

    # Warehouse-only user gets a 403
    def test_no_warehouse_access(self):
        url = reverse('client:home')

        self.test_client.login(username='warehouse_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 403)

    # Accounting-only user gets a 403
    def test_no_accounting_access(self):
        url = reverse('client:home')

        self.test_client.login(username='accounting_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 403)

    # User with a proper ClientUser linkage gets access
    def test_client_access(self):
        url = reverse('client:home')

        self.test_client.login(username='client_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

    # Invalid login gets punted to the login page
    def test_invalid_login(self):
        url = reverse('client:home')

        self.test_client.login(username='admin_user@example.com', password='bad-password')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:login'))

    # Inactive user gets punted to the login page
    def test_inactive_user(self):
        url = reverse('client:home')

        self.test_client.login(username='inactive_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:login'))

    def test_valid_user_with_no_clients(self):
        url = reverse('client:home')

        self.test_client.login(username='client_user@example.com', password='test123')
        self.client_user.clientuser_set.all().delete()
        response = self.test_client.get(url)
        self.assertContains(response, 'No clients assigned to user', status_code=403)

    def test_user_with_access_to_client_ancestor(self):
        url = reverse('client:home')
        session = self.test_client.session
        session['selected_client_id'] = self.child_client.id
        session.save()

        self.test_client.login(username='client_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

    def test_user_with_unassigned_selected_client_and_valid_client(self):
        url = reverse('client:home')
        session = self.test_client.session
        session['selected_client_id'] = self.other_client.id
        session.save()

        self.test_client.login(username='client_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

    def test_user_with_unassigned_selected_client_and_no_valid_client(self):
        url = reverse('client:home')
        session = self.test_client.session
        session['selected_client_id'] = self.other_client.id
        session.save()

        self.client_user.clientuser_set.all().delete()
        self.test_client.login(username='client_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertContains(response, 'No clients assigned to user', status_code=403)

    def test_user_with_nonexistent_selected_client_and_valid_client(self):
        url = reverse('client:home')
        session = self.test_client.session
        session['selected_client_id'] = 100
        session.save()

        self.test_client.login(username='client_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

    def test_user_with_nonexistent_selected_client_and_no_valid_client(self):
        url = reverse('client:home')
        session = self.test_client.session
        session['selected_client_id'] = 100
        session.save()

        self.client_user.clientuser_set.all().delete()
        self.test_client.login(username='client_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertContains(response, 'No clients assigned to user', status_code=403)

    # User can select any client to which he has a ClientUser linkage
    # Admin user with no ClientUser linkages gets access
    # Admin user with a ClientUser linkage gets access
    # Admin user can select any valid client
