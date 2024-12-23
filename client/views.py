# -*- coding: utf-8 -*-


from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from django.db.models import Sum
from django.contrib.auth import authenticate, login

#from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
#from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from ims.models import Product, Transaction, Shipment, Client, ClientUser, Location
from ims.forms import UserLoginForm
from ims.views import LoginView
from ims.tasks import email_purchase_order, email_delivery_request, sps_submit_shipment
from ims.sps import SPSService

from datetime import datetime, timedelta
import json
import re

import logging
logger = logging.getLogger(__name__)

PASSWORD_REGEX = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
PASSWORD_COMPLEXITY = 'minimum 8 characters, at least one letter, one number and one special character'

company_info = {
    'name': settings.COMPANY_NAME,
    'site_email': settings.SITE_EMAIL,
    'support_email': settings.SUPPORT_EMAIL,
    'phone_number': settings.COMPANY_PHONE_NUMBER,
    'password_complexity': PASSWORD_COMPLEXITY,
}


class LoginView(LoginView):
    template_name = 'client/login.html'
    home_url = reverse_lazy('client:home')
#    form_list = (
#        ('auth', UserLoginForm),
#        ('token', AuthenticationTokenForm),
#        ('backup', BackupTokenForm),
#    )


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

    current_password = request.POST.get('current_password')
    new_password_1 = request.POST.get('new_password_1')
    new_password_2 = request.POST.get('new_password_2')

    if not authenticate(username=request.user.email, password=current_password):
        logger.info(f'Password change failure for {request.user}: current password incorrect.')
        return JsonResponse({'success': False, 'message': 'Current password was not correct.'})

    if new_password_1 != new_password_2:
        logger.info(f'Password change failure for {request.user}: passwords did not match.')
        return JsonResponse({'success': False, 'message': 'Passwords did not match.'})

    if not re.match(PASSWORD_REGEX, new_password_1):
        logger.info(f'Password change failure for {request.user}: password complexity insufficient.')
        return JsonResponse({'success': False, 'message': f'Password does not meet the complexity requirements ({PASSWORD_COMPLEXITY}).'})

    if authenticate(username=request.user.email, password=new_password_1):
        logger.info(f'Password change failure for {request.user}: new password same as current password.')
        return JsonResponse({'success': False, 'message': f'Password cannot be the same as your existing password.'})

    request.user.set_password(new_password_1)
    request.user.save()
    login(request, request.user)

    logger.info(f'{request.user} changed their password')

    return JsonResponse({'success': True})


@require_POST
def dismiss_password_prompt(request):
    request.user.date_password_prompt_dismissed = timezone.now()
    request.user.save()

    logger.info(f'{request.user} dismissed the password change prompt')

    return JsonResponse({'success': True})


@require_POST
def select_client(request, client_id):
    client = get_object_or_404(Client, pk=client_id, is_active=True)
    if not request.user.is_admin:
        try:
            if ClientUser.objects.filter(user=request.user, client__id__in=client.ancestors).count() == 0:
                return JsonResponse({'success': False, 'message': 'Invalid client selected.'})
        except Exception as e:
            logger.warning('Failed to select client {0}: {1}'.format(client, e))
            return JsonResponse({'success': False, 'message': 'Invalid client selected.'})
    request.session['selected_client_id'] = client.id
    return JsonResponse({'success': True})


def profile(request):
    primary_contact = request.selected_client.clientuser_set.filter(is_primary=True).first()

    context = {
        'company_info': company_info,
        'primary_contact': primary_contact,
    }
    return render(request, 'client/profile.html', context)


def profile_locations(request):
    locations = Location.objects.filter(client=request.selected_client, is_active=True).order_by('name')
    context = {
        'locations': locations,
    }
    return render(request, 'client/locations_list.html', context)


def profile_location_detail(request, location_id):
    location = get_object_or_404(Location, pk=location_id, is_active=True, client=request.selected_client)
    context = {
        'location': location,
    }
    return render(request, 'client/location_detail.html', context)


def inventory(request):
    logger.info(f'{request.user} {request.META.get("HTTP_X_FORWARDED_FOR")} viewed client inventory page for {request.selected_client}')

    locations = []
    if request.selected_client:
        locations = Location.objects.filter(client__in=[c['obj'] for c in request.selected_client.children], is_active=True).order_by('name')

    context = {
        'company_info': company_info,
        'locations': locations,
        'shipmentid': request.GET.get('shipmentid', None),
    }
    return render(request, 'client/inventory.html', context)


def inventory_list(request):
    shipment_product_cases = {}
    shipment_id = request.GET.get('shipmentid', None)
    shipment = None
    if shipment_id:
        shipment = get_object_or_404(Shipment, pk=shipment_id)
        for transaction in shipment.transaction_set.all():
            shipment_product_cases[transaction.product.id] = transaction.cases

    filter_clients = []
    if request.selected_client:
        filter_clients = [c['obj'] for c in request.selected_client.children]

    tab = request.GET.get('tab', 'request')
    context = {
        'shipment': shipment,
        'tab': tab,
    }

    if tab == 'request':

        products = []
        if request.selected_client:
            for product in Product.objects.filter(client__in=filter_clients, is_deleted=False, is_active=True).order_by('client_tag', 'name', 'item_number'):
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


def delivery_products(request, shipment_id):
    shipment = get_object_or_404(Shipment, pk=shipment_id)

    context = {
        'shipment': shipment,
    }
    return render(request, 'client/delivery_products.html', context)


@require_POST
def inventory_request_delivery(request):

    # First validate the JSON data in the request
    if not 'json' in request.POST:
        return JsonResponse({'success': False, 'message': 'Malformed request.'})
    try:
        delivery_data = json.loads(request.POST['json'])
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

    logger.info(delivery_data)
    logger.info(f'Selected client: {request.selected_client}')

    # Check all requested products for validity and availability
    requested_products = []
    for requested_product in delivery_data['products']:
        try:
            product = Product.objects.get(pk=requested_product['productid'])
        except Product.DoesNotExist:
            logger.info(f"Invalid product ID requested: {requested_product['productid']}")
            return JsonResponse({'success': False, 'message': 'Invalid product ID {0}.'.format(requested_product['productid'])})
        if not request.selected_client.id in product.client.ancestors:
            logger.info(f"Selected client not in product client hierarchy: {request.selected_client.id} {product}")
            return JsonResponse({'success': False, 'message': 'Invalid product ID {0}.'.format(requested_product['productid'])})

        requested_cases = int(requested_product.get('cases', 0) or 0)
        if requested_cases == 0:
            continue

        if requested_cases > product.cases_available or requested_cases < 0:
            logger.info(f"Invalid product quantity requested: {requested_cases} for {product}")
            return JsonResponse({'success': False, 'message': 'Invalid number of cases requested for product {0}.'.format(product.item_number)})
        requested_products.append({
            'obj': product,
            'cases': requested_cases,
        })

    # Validate location of delivery
    try:
        location = Location.objects.get(pk=delivery_data['locationid'])
    except Location.DoesNotExist:
        logger.info(f"Invalid location: {delivery_data['locationid']}")
        return JsonResponse({'success': False, 'message': 'Invalid location.'})

    requesting_user = request.user

    # Validate on-behalf-of user
    on_behalf_of = delivery_data.get('on_behalf_of')
    if on_behalf_of:
        try:
            client_user = request.selected_client.contacts.get(pk=on_behalf_of)
            requesting_user = client_user.user
        except ClientUser.DoesNotExist:
            pass

    # If we're editing a previous shipment request, pull that shipment and clear
    # out all transactions. Otherwise, create a new shipment
    shipment_updated = False
    if delivery_data['shipmentid']:
        try:
            shipment = Shipment.objects.get(pk=delivery_data['shipmentid'])
        except Shipment.DoesNotExist:
            logger.info(f"Invalid shipment ID: {delivery_data['shipmentid']}")
            return JsonResponse({'success': False, 'message': 'Invalid shipment ID.'})
        Transaction.objects.filter(shipment=shipment).delete()
        shipment_updated = True
    else:
        shipment = Shipment(
            client=request.selected_client,
            user=requesting_user,
            status=Shipment.Status.PENDING,
        )

    shipment.location = location
    shipment.purchase_order_number = delivery_data.get('client_po')
    try:
        shipment.purchase_order_deadline = datetime.strptime(delivery_data.get('po_deadline') or '', '%m/%d/%Y')
    except ValueError:
        pass
    shipment.save()

    if shipment_updated:
        logger.info(f'{request.user} {request.META.get("HTTP_X_FORWARDED_FOR")} updated delivery request {shipment} for {request.selected_client}')
    else:
        logger.info(f'{request.user} {request.META.get("HTTP_X_FORWARDED_FOR")} created delivery request {shipment} for {request.selected_client}')
    logger.info(f'Location: {location}')
    if on_behalf_of:
        logger.info(f'On behalf of {requesting_user}')

    # Create new transactions for each requested product
    total_cases = 0
    for product in requested_products:
        transaction = Transaction(
            product=product['obj'],
            is_outbound=True,
            shipment=shipment,
            client=request.selected_client,
            cases=product['cases'],
        )
        transaction.save()
        logger.info(f'{transaction.cases}\t{transaction.product}')
        total_cases += product['cases']

    # Send a notification email to the configured delivery admin
    email_delivery_request.delay(
        shipment_id=shipment.id, shipment_updated=shipment_updated, client_email=requesting_user.email
    )
    logger.info('Launched email_delivery_request task')

    # Generate PO PDF and email to PO address
    email_purchase_order.delay(shipment_id=shipment.id)
    logger.info('Launched email_purchase_order task')

    # Submit shipment payload to SPS
    if settings.SPS_ENABLE and settings.SPS_SUBMIT_ON_CREATE:
        sps_submit_shipment.delay(shipment.id)
        logger.info('Launched sps_submit_shipment task')

    logger.info(f'Shipment {shipment.id} submitted successfully.')
    return JsonResponse({'success': True, 'shipment_id': shipment.id})


def history(request):
    logger.info(f'{request.user} viewed client history page for {request.selected_client}')

    products = None
    if request.selected_client:
        products = request.selected_client.product_set.filter(is_deleted=False, is_active=True).order_by('item_number')

    context = {
        'company_info': company_info,
        'products': products,
    }
    return render(request, 'client/history.html', context)


def reorder(request):

    products = None
    if request.selected_client:
        products = request.selected_client.product_set.filter(is_deleted=False, is_active=True).order_by('item_number')

    context = {
        'company_info': company_info,
        'products': products,
    }
    return render(request, 'client/reorder.html', context)


def product_history(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if not request.user.is_authorized_for_client(product.client):
        raise Http404

    date_to = timezone.now().date() + timedelta(days=30)
    date_from = timezone.now().date() - timedelta(days=365)
    try:
        date_from = datetime.strptime(request.GET.get('fromdate', ''), '%m/%d/%Y').date()
        date_to = datetime.strptime(request.GET.get('todate', ''), '%m/%d/%Y').date()
    except:
        pass

    # history = Transaction.objects.filter(product=product, date_created__gt=date_from, date_created__lte=date_to).order_by('-date_created')

#    request.session['selected_client_id'] = 241

    context = {
        'product': product,
        'history': product.get_history(date_from),
        'date_from': date_from,
        'date_to': date_to,
    }
    logger.info(f'{request.user} viewed product history for {product} ({request.selected_client}) - {date_from} to {date_to}')
    return render(request, 'client/product_history.html', context)


def product_report(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if not request.user.is_authorized_for_client(product.client):
        raise Http404

    date_to = timezone.now().date() + timedelta(days=30)
    date_from = timezone.now().date() - timedelta(days=365)
    try:
        date_from = datetime.strptime(request.GET.get('fromdate', ''), '%m/%d/%Y').date()
        date_to = datetime.strptime(request.GET.get('todate', ''), '%m/%d/%Y').date()
    except:
        pass

    cleaned_name = product.name.replace('\'', r'′').replace('"', '″')

    context = {
        'product': product,
        'chart_title': f'{product.item_number} {cleaned_name}',
        'history': product.get_history(date_from),
        'date_from': date_from,
        'date_to': date_to,
    }

    logger.info(f'{request.user} viewed product history report for {product} ({request.selected_client})')
    return render(request, 'client/product_report.html', context)


def shipment_docs(request, shipment_id):
    shipment = get_object_or_404(Shipment, pk=shipment_id)

    context = {
        'shipment': shipment,
    }
    return render(request, 'client/shipment_docs.html', context)


