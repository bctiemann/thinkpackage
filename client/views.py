# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

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


def client_profile(request):

    context = {
    }
    return render(request, 'client/profile.html', context)


def client_inventory(request):

    child_clients = []
    client_users = ClientUser.objects.filter(user=request.user, client__is_active=True)
    for cu in client_users:
        children_of_other = utils.list_at_node(utils.tree_to_list(Client.objects.filter(is_active=True), sort_by='company_name'), cu.client)
        for child in children_of_other:
            if not child in child_clients:
                child['indent_rendered'] = '&nbsp;&nbsp;&nbsp;&nbsp;'.join(['' for i in xrange(child['depth'] + 1)])
                child_clients.append(child)

    if 'selected_client_id' in request.session:
        try:
            selected_client = ClientUser.objects.get(user=request.user, client__id=request.session['selected_client_id']).client
        except:
            selected_client = ClientUser.objects.filter(user=request.user, client__is_active=True).first()
    else:
        selected_client = ClientUser.objects.filter(user=request.user, client__is_active=True).first()

    children_of_selected = utils.list_at_node(utils.tree_to_list(Client.objects.filter(is_active=True), sort_by='company_name'), selected_client)

    context = {
#        'selected_client': request.user.get_selected_client(request),
        'child_clients': child_clients,
        'selected_client': selected_client,
    }
    return render(request, 'client/inventory.html', context)


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
