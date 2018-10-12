# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from django.db.models import Sum
from django.contrib.auth import authenticate, login

from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from ims.models import Product, Transaction, Shipment, Client, ClientUser, Location
from ims.forms import UserLoginForm
from ims import utils

from datetime import datetime, timedelta
import json
import re

import logging
logger = logging.getLogger(__name__)


company_info = {
    'name': settings.COMPANY_NAME,
    'site_email': settings.SITE_EMAIL,
    'phone_number': settings.COMPANY_PHONE_NUMBER,
}


class LoginView(LoginView):
    template_name = 'client/login.html'
    form_list = (
        ('auth', UserLoginForm),
        ('token', AuthenticationTokenForm),
        ('backup', BackupTokenForm),
    )


#class PhoneSetupView(PhoneSetupView):
#    success_url = reverse_lazy('two_factor:profile')


#class PhoneDeleteView(PhoneDeleteView):
#    success_url = reverse_lazy('two_factor:profile')


#class DisableView(DisableView):
#    success_url = reverse_lazy('two_factor:profile')


def home(request):
    return redirect('client:inventory')


@require_POST
def change_password(request):
    passwd_regex = '(?=^.{6,255}$)((?=.*\d)(?=.*[A-Z])(?=.*[a-z])|(?=.*\d)(?=.*[^A-Za-z0-9])(?=.*[a-z])|(?=.*[^A-Za-z0-9])(?=.*[A-Z])(?=.*[a-z])|(?=.*\d)(?=.*[A-Z])(?=.*[^A-Za-z0-9]))^.*'

    current_password = request.POST.get('current_password')
    new_password_1 = request.POST.get('new_password_1')
    new_password_2 = request.POST.get('new_password_2')

    if not authenticate(username=request.user.email, password=current_password):
        return JsonResponse({'success': False, 'message': 'Current password was not correct.'})

    if new_password_1 != new_password_2:
        return JsonResponse({'success': False, 'message': 'Passwords did not match.'})

    if not re.match(passwd_regex, new_password_1):
        return JsonResponse({'success': False, 'message': 'Password does not meet the complexity requirements.'})

    request.user.set_password(new_password_1)
    request.user.save()
    login(request, request.user)

    return JsonResponse({'success': True})


@require_POST
def select_client(request, client_id):
    client = get_object_or_404(Client, pk=client_id, is_active=True)
    try:
        if ClientUser.objects.filter(user=request.user, client__id__in=client.ancestors).count() == 0:
            return JsonResponse({'success': False, 'message': 'Invalid client selected.'})
    except Exception, e:
        logger.warning('Failed to select client {0}: {1}'.format(client, e))
        return JsonResponse({'success': False, 'message': 'Invalid client selected.'})
    request.session['selected_client_id'] = client.id
    return JsonResponse({'success': True})


def client_profile(request):
    primary_contact = request.selected_client.clientuser_set.filter(is_primary=True).first()

    context = {
        'company_info': company_info,
        'primary_contact': primary_contact,
    }
    return render(request, 'client/profile.html', context)


def client_profile_locations(request):
    locations = Location.objects.filter(client=request.selected_client, is_active=True).order_by('name')
    context = {
        'locations': locations,
    }
    return render(request, 'client/locations_list.html', context)


def client_profile_location_detail(request, location_id):
    location = get_object_or_404(Location, pk=location_id, is_active=True, client=request.selected_client)
    context = {
        'location': location,
    }
    return render(request, 'client/location_detail.html', context)


def client_inventory(request):
    locations = Location.objects.filter(client__in=[c['obj'] for c in request.selected_client.children], is_active=True).order_by('name')

    context = {
        'company_info': company_info,
        'locations': locations,
        'shipmentid': request.GET.get('shipmentid', None),
    }
    return render(request, 'client/inventory.html', context)


def client_inventory_list(request):
    shipment_product_cases = {}
    shipment_id = request.GET.get('shipmentid', None)
    shipment = None
    if shipment_id:
        shipment = get_object_or_404(Shipment, pk=shipment_id)
        for transaction in shipment.transaction_set.all():
            shipment_product_cases[transaction.product.id] = transaction.cases

    filter_clients = [c['obj'] for c in request.selected_client.children]

    tab = request.GET.get('tab', 'request')
    context = {
        'shipment': shipment,
        'tab': tab,
    }

    if tab == 'request':

        products = []
        if request.selected_client:
            for product in Product.objects.filter(client__in=filter_clients, is_deleted=False, is_active=True).order_by('item_number'):
                shipment_cases = None
                if shipment and product.id in shipment_product_cases:
                    shipment_cases = shipment_product_cases[product.id]
                products.append((product, shipment_cases))

        context['products'] = products

    elif tab == 'pending':

        context['shipments'] = Shipment.objects.filter(client__in=filter_clients, date_shipped__isnull=True)

    elif tab == 'shipped':

        context['shipments'] = Shipment.objects.filter(client__in=filter_clients, date_shipped__isnull=False)


    return render(request, 'client/inventory_list.html', context)


def client_delivery_products(request, shipment_id):
    shipment = get_object_or_404(Shipment, pk=shipment_id)

    context = {
        'shipment': shipment,
    }
    return render(request, 'client/delivery_products.html', context)


@require_POST
def client_inventory_request_delivery(request):

    # First validate the JSON data in the request
    if not 'json' in request.POST:
        return JsonResponse({'success': False, 'message': 'Malformed request.'})
    try:
        delivery_data = json.loads(request.POST['json'])
    except Exception, e:
        return JsonResponse({'success': False, 'message': str(e)})

    # Check all requested products for validity and availability
    requested_products = []
    for requested_product in delivery_data['products']:
        try:
            product = Product.objects.get(pk=requested_product['productid'], client=request.selected_client)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid product ID {0}.'.format(requested_product['productid'])})
        if requested_product['cases'] > product.cases_available:
            return JsonResponse({'success': False, 'message': 'Invalid number of cases requested for product {0}.'.format(product.item_number)})
        requested_products.append({
            'obj': product,
            'cases': requested_product['cases'],
        })

    # Validate location of delivery
    try:
        location = Location.objects.get(pk=delivery_data['locationid'])
    except Location.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid location.'})

    # If we're editing a previous shipment request, pull that shipment and clear
    # out all transactions. Otherwise, create a new shipment
    shipment_updated = False
    if delivery_data['shipmentid']:
        try:
            shipment = Shipment.objects.get(pk=delivery_data['shipmentid'])
        except Shipment.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid shipment ID.'})
        Transaction.objects.filter(shipment=shipment).delete()
        shipment_updated = True
    else:
        shipment = Shipment(
            client = request.selected_client,
            user = request.user,
            status = 0,
        )

    shipment.location = location
    shipment.save()

    # Create new transactions for each requested product
    total_cases = 0
    for product in requested_products:
        transaction = Transaction(
            product = product['obj'],
            is_outbound = True,
            shipment = shipment,
            client = request.selected_client,
            cases = product['cases'],
        )
        transaction.save()
        total_cases += requested_product['cases']

    # Send a notification email to the configured delivery admin
    context = {
        'user': request.user,
        'shipment': shipment,
        'client': request.selected_client,
        'location': location,
        'total_cases': total_cases,
        'requested_products': requested_products,
        'shipment_updated': shipment_updated,
    }

    utils.send_templated_email(
        [settings.DELIVERY_EMAIL],
        context,
        'Delivery Order #{0} - {1}'.format(shipment.id, selected_client.company_name),
        'email/delivery_request.txt',
        'email/delivery_request.html',
    )

    return JsonResponse({'success': True})


def client_history(request):

    products = None
    if request.selected_client:
        products = request.selected_client.product_set.filter(is_deleted=False, is_active=True).order_by('item_number')

    context = {
        'company_info': company_info,
        'products': products,
    }
    return render(request, 'client/history.html', context)


def client_reorder(request):

    products = None
    if request.selected_client:
        products = request.selected_client.product_set.filter(is_deleted=False, is_active=True).order_by('item_number')

    context = {
        'company_info': company_info,
        'products': products,
    }
    return render(request, 'client/reorder.html', context)


def client_product_history(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    date_to = timezone.now() + timedelta(days=30)
    date_from = timezone.now() - timedelta(days=365)
    try:
        date_from = datetime.strptime(request.GET.get('fromdate', ''), '%m/%d/%Y')
        date_to = datetime.strptime(request.GET.get('todate', ''), '%m/%d/%Y')
    except:
        pass

    history = Transaction.objects.filter(product=product, date_created__gt=date_from, date_created__lte=date_to).order_by('-date_created')

#    request.session['selected_client_id'] = 241

    context = {
        'product': product,
        'history': history,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'client/product_history.html', context)


def client_shipment_docs(request, shipment_id):
    shipment = get_object_or_404(Shipment, pk=shipment_id)

    context = {
        'shipment': shipment,
    }
    return render(request, 'client/shipment_docs.html', context)
