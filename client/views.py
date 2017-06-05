# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden

from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from ims.models import Product, Transaction, Shipment, Client, ClientUser
from ims.forms import UserLoginForm
from ims import utils

from datetime import datetime, timedelta

import logging
logger = logging.getLogger(__name__)


class LoginView(LoginView):
    template_name = 'client/login.html'
    form_list = (
        ('auth', UserLoginForm),
        ('token', AuthenticationTokenForm),
        ('backup', BackupTokenForm),
    )


class PhoneSetupView(PhoneSetupView):
    success_url = reverse_lazy('two_factor:profile')


class PhoneDeleteView(PhoneDeleteView):
    success_url = reverse_lazy('two_factor:profile')


class DisableView(DisableView):
    success_url = reverse_lazy('two_factor:profile')


def client(request):
    return redirect('client-inventory')


@require_POST
def select_client(request, client_id):
#    client_user = get_object_or_404(ClientUser, user=request.user, client=client_id, client__is_active=True)
#    client = client_user.client
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

    context = {
    }
    return render(request, 'client/profile.html', context)


def client_inventory(request):

    context = {
        'selected_client': request.user.get_selected_client(request),
        'children_of_selected': request.user.get_children_of_selected(request),
        'shipmentid': request.GET.get('shipmentid', 'null'),
    }
    return render(request, 'client/inventory.html', context)


def client_inventory_list(request):
    shipment_product_cases = {}
    shipment_id = request.GET.get('shipmentid', None)
    if shipment_id:
        shipment = get_object_or_404(Shipment, pk=shipment_id)
        for transaction in shipment.transaction_set.all():
            shipment_product_cases[transaction.product.id] = transaction.cases

    selected_client = request.user.get_selected_client(request)
    products = []
    if selected_client:
        for product in selected_client.product_set.filter(is_deleted=False, is_active=True).order_by('item_number'):
            shipment_cases = None
            if shipment and product.id in shipment_product_cases:
                shipment_cases = shipment_product_cases[product.id]
            products.append((product, shipment_cases))

    context = {
        'selected_client': selected_client,
        'products': products,
        'tab': request.GET.get('tab', 'request'),
    }
    return render(request, 'client/inventory_list.html', context)


def client_history(request):

    selected_client = request.user.get_selected_client(request)
    products = None
    if selected_client:
        products = selected_client.product_set.filter(is_deleted=False, is_active=True).order_by('item_number')

    context = {
        'selected_client': selected_client,
        'products': products,
    }
    return render(request, 'client/history.html', context)


def client_reorder(request):

    selected_client = request.user.get_selected_client(request)
    products = None
    if selected_client:
        products = selected_client.product_set.filter(is_deleted=False, is_active=True).order_by('item_number')

    context = {
        'selected_client': selected_client,
        'products': products,
    }
    return render(request, 'client/reorder.html', context)


def client_product_history(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    date_to = timezone.now()
    date_from = date_to - timedelta(days=90)
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
