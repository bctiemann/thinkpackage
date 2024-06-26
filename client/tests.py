from decimal import Decimal
import json

from django.test import TestCase, Client as TestClient
from django.urls import reverse, reverse_lazy

from ims.models import Client, ClientUser, Location, User, Product, Shipment, Transaction, Receivable
from ims.tests import ajax_headers


class AuthTestCase(TestCase):
    fixtures = ['Client', 'User', 'Location', 'Product', 'ShipperAddress', 'Shipment', 'ShipmentDoc']

    def setUp(self):
        self.test_client = TestClient()
        self.client = Client.objects.get(company_name='Client 1')
        self.child_client = Client.objects.get(company_name='Child Client')
        self.other_client = Client.objects.get(company_name='Client 2')
        self.client_user = User.objects.get(email='client_user@example.com')
        self.admin_user = User.objects.get(email='admin_user@example.com')
        self.client_A = Client.objects.get(company_name='A')
        self.client_B = Client.objects.get(company_name='B')
        self.client_C = Client.objects.get(company_name='C')

    # Admin user (with no client linkages) has access to client site
    def test_admin_access(self):
        url = reverse('client:home')

        self.test_client.login(username='admin_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

        response = self.test_client.get(response.url)
        self.assertContains(response, '<option value="4" selected>A</option>')

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

        response = self.test_client.get(response.url)
        self.assertNotContains(response, 'No client is selected. Please select a client from the menu at the top.')

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

    # Authenticated user not authorized for any clients gets a 403
    def test_valid_user_with_no_clients(self):
        url = reverse('client:home')

        self.test_client.login(username='client_user@example.com', password='test123')
        self.client_user.clientuser_set.all().delete()
        response = self.test_client.get(url)
        self.assertContains(response, 'No clients assigned to user', status_code=403)

    # User with a linkage to an ancestor client of selected client gets access
    def test_user_with_access_to_client_ancestor(self):
        url = reverse('client:home')
        session = self.test_client.session
        session['selected_client_id'] = self.child_client.id
        session.save()

        self.test_client.login(username='client_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

    # User with a linkage to a valid client that is not the client saved in the session gets access to the valid one
    def test_user_with_unassigned_selected_client_and_valid_client(self):
        url = reverse('client:home')
        session = self.test_client.session
        session['selected_client_id'] = self.other_client.id
        session.save()

        self.test_client.login(username='client_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

    # User with no valid client linkages and with an unauthorized client saved in the session gets a 403
    def test_user_with_unassigned_selected_client_and_no_valid_client(self):
        url = reverse('client:home')
        session = self.test_client.session
        session['selected_client_id'] = self.other_client.id
        session.save()

        self.client_user.clientuser_set.all().delete()
        self.test_client.login(username='client_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertContains(response, 'No clients assigned to user', status_code=403)

    # User with a linkage to a nonexistent client and with a valid linkage to a real client gets access to the valid one
    def test_user_with_nonexistent_selected_client_and_valid_client(self):
        url = reverse('client:home')
        session = self.test_client.session
        session['selected_client_id'] = 100
        session.save()

        self.test_client.login(username='client_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

    # User with a linkage to a nonexistent client and with no valid linkages gets a 403
    def test_user_with_nonexistent_selected_client_and_no_valid_client(self):
        url = reverse('client:home')
        session = self.test_client.session
        session['selected_client_id'] = 100
        session.save()

        self.client_user.clientuser_set.all().delete()
        self.test_client.login(username='client_user@example.com', password='test123')
        response = self.test_client.get(url)
        self.assertContains(response, 'No clients assigned to user', status_code=403)

    # User can switch from one selected client to another valid one
    def test_select_valid_client(self):
        session = self.test_client.session
        session['selected_client_id'] = self.client.id
        session.save()
        url = reverse('client:select', kwargs={'client_id': self.child_client.id})

        self.test_client.login(username='client_user@example.com', password='test123')
        payload = {}
        response = self.test_client.post(url, payload, **ajax_headers)
        result = json.loads(response.content)
        self.assertTrue(result['success'])

    # User cannot switch from a valid client to an unauthorized one
    def test_select_invalid_client(self):
        session = self.test_client.session
        session['selected_client_id'] = self.client.id
        session.save()
        url = reverse('client:select', kwargs={'client_id': self.other_client.id})

        self.test_client.login(username='client_user@example.com', password='test123')
        payload = {}
        response = self.test_client.post(url, payload, **ajax_headers)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'Invalid client selected.')

    # Admin user can select any client
    def test_admin_user_can_select_unassigned_client(self):
        session = self.test_client.session
        session['selected_client_id'] = self.client.id
        session.save()
        url = reverse('client:select', kwargs={'client_id': self.other_client.id})

        self.test_client.login(username='admin_user@example.com', password='test123')
        payload = {}
        response = self.test_client.post(url, payload, **ajax_headers)
        result = json.loads(response.content)
        self.assertTrue(result['success'])

    # Ensure a client can login with mixed case email
    def test_mixed_case_email(self):
        url = reverse('client:home')

        self.test_client.login(username='Client_User@Example.com', password='test123')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('client:inventory'))

    # Hierarchy of clients: A -> B -> C (A at top)
    # User is assigned to B
    # User should have access to B and C
    def test_hierarchical_permissions(self):
        self.assertFalse(self.client_user.is_authorized_for_client(self.client_A))
        self.assertTrue(self.client_user.is_authorized_for_client(self.client_B))
        self.assertTrue(self.client_user.is_authorized_for_client(self.client_C))

    def test_client_can_download_own_document(self):
        self.test_client.login(username='client_user@example.com', password='test123')

        url = reverse('shipment-doc', kwargs={'doc_id': '34b0587c-af09-0591-c66b-39a9faac2a71'})
        response = self.test_client.get(url)
        self.assertNotEqual(response.status_code, 403)

        # Doc for client_A - not allowed
        url = reverse('shipment-doc', kwargs={'doc_id': '34b0587c-af09-0591-c66b-39a9faac2a72'})
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 403)

        # Doc for client_B - allowed
        url = reverse('shipment-doc', kwargs={'doc_id': '34b0587c-af09-0591-c66b-39a9faac2a73'})
        response = self.test_client.get(url)
        self.assertNotEqual(response.status_code, 403)

        # Doc for client_C - allowed
        url = reverse('shipment-doc', kwargs={'doc_id': '34b0587c-af09-0591-c66b-39a9faac2a74'})
        response = self.test_client.get(url)
        self.assertNotEqual(response.status_code, 403)

        # Doc for unrelated client - not allowed
        url = reverse('shipment-doc', kwargs={'doc_id': '34b0587c-af09-0591-c66b-39a9faac2a75'})
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 403)


class ProfileTestCase(TestCase):
    fixtures = ['User', 'Client', 'Location']

    def setUp(self):
        self.test_client = TestClient()
        self.client = Client.objects.get(company_name='Client 1')
        self.child_client = Client.objects.get(company_name='Child Client')
        self.other_client = Client.objects.get(company_name='Client 2')
        self.client_user = User.objects.get(email='client_user@example.com')
        self.admin_user = User.objects.get(email='admin_user@example.com')
        self.test_client.login(username='client_user@example.com', password='test123')

    def test_list_locations(self):
        url = reverse('client:profile-locations')
        response = self.test_client.get(url)
        self.assertContains(response, 'Location 1')
        self.assertContains(response, 'Location 2')
        self.assertContains(response, 'Location 3')

    def test_location_detail(self):
        url = reverse('client:profile-location-detail', kwargs={'location_id': 225})
        response = self.test_client.get(url)
        self.assertContains(response, 'Location 1')

    def test_location_detail_child_client(self):
        url = reverse('client:profile-location-detail', kwargs={'location_id': 228})
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_location_detail_other_client(self):
        url = reverse('client:profile-location-detail', kwargs={'location_id': 229})
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 404)

    # Even admin user can't pull data for a location belonging to a client other than the selected_client
    def test_location_detail_other_client_admin_user(self):
        self.test_client.login(username='admin_user@example.com', password='test123')
        url = reverse('client:profile-location-detail', kwargs={'location_id': 229})
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 404)


class InventoryTestCase(TestCase):
    fixtures = ['User', 'Client', 'Location', 'Product', 'ShipperAddress']

    def setUp(self):
        self.test_client = TestClient()
        self.client = Client.objects.get(company_name='Client 1')
        self.child_client = Client.objects.get(company_name='Child Client')
        self.other_client = Client.objects.get(company_name='Client 2')
        self.client_user = User.objects.get(email='client_user@example.com')
        self.admin_user = User.objects.get(email='admin_user@example.com')
        self.test_client.login(username='client_user@example.com', password='test123')

    def test_list_inventory(self):
        url = reverse('client:inventory-list')
        response = self.test_client.get(url)
        self.assertContains(response, '6PC Macaron Box')
        self.assertContains(response, 'Pastry Box Small')
        self.assertContains(response, 'Pastry Box Out of Stock')

    # TODO: More assertions and checks on artifacts
    def test_request_delivery(self):
        url = reverse('client:inventory-request_delivery')
        payload = {
            'products': [
                {
                    'productid': '274',
                    'cases': 2,
                },
                {
                    'productid': '275',
                    'cases': 5,
                },
            ],
            'locationid': '225',
            'customerid': '',
            'shipmentid': 0,
            'client_po': 'Test PO',
            'po_deadline': '12/20/2021',
            'on_behalf_of': '',
        }
        json_payload = {'json': json.dumps(payload)}
        response = self.test_client.post(url, json_payload, **ajax_headers)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        shipment = Shipment.objects.filter(pk=result['shipment_id']).first()
        self.assertIsNotNone(shipment)
        self.assertEqual(shipment.transaction_set.count(), 2)

    # TODO:
    # Test email is sent
    # Test requesting products not in requested_client
    # Test requesting products in children of requested_client
    # Test requesting products not in children of requested_client
    # Test invalid products
    # Test on-behalf-of functionality
    # Test selected location
    # Test invalid location
