# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.db.models import Func, F, Count

from ims.models import Client, Shipment, Transaction, Product
from ims import utils

import logging
logger = logging.getLogger(__name__)


def home(request):
    context = {
    }
    return render(request, 'ims/home.html', context)


def mgmt(request):

    delivery_requests = Shipment.objects.exclude(status=2).order_by('-date_created')

    ready_to_ship = Shipment.objects.filter(status=1).order_by('-date_created')

    inbound_receivables = []
    for receivable in Transaction.objects.filter(is_outbound=False, cases__isnull=True).order_by('-date_created'):
        split_receivables = Transaction.objects.filter(
            product=receivable.product,
            receivable__purchase_order=receivable.receivable.purchase_order,
            receivable__shipment_order=receivable.receivable.shipment_order,
            cases__isnull=False
        )
        inbound_receivables.append({
            'obj': receivable,
            'is_partial': split_receivables.count() > 0,
        })

    invq = Shipment.objects.filter(status=2, transaction__product__account_prepay_type=1, accounting_status__in=[0, 1]) \
        .order_by('-date_created') \
        .annotate(date=Func(F('date_created'), function='DATE')) \
        .values('date', 'id', 'client__company_name', 'location__name', 'client__id') \
        .annotate(count=Count('date'))

    low_stock = []
    for product in Product.objects.filter(cases_inventory__lt=F('contracted_quantity') / 2, is_active=True).order_by('name'):
        try:
            last_shipment = Transaction.objects.filter(product=product).order_by('-date_created').first()
            low_stock.append({
                'obj': product,
                'last_shipment': last_shipment,
            })
        except Transaction.DoesNotExist:
            pass

    context = {
        'delivery_requests': delivery_requests,
        'ready_to_ship': ready_to_ship,
        'inbound_receivables': inbound_receivables,
        'invq': invq,
        'low_stock': low_stock,
    }
    return render(request, 'ims/mgmt.html', context)


def mgmt_redirect(request, client_id=None):
    return redirect('mgmt-inventory', client_id=client_id)


def mgmt_inventory(request, client_id=None):
    context = {
        'client_id': client_id,
    }
    return render(request, 'ims/mgmt_inventory.html', context)


def mgmt_customers_list(request):
    filter = request.GET.get('filter', None)

    clients = Client.objects.all().order_by('company_name')

    if filter == 'warehousing':
        clients = clients.filter(has_warehousing=True, is_active=True)
    elif filter == 'no-warehousing':
        clients = clients.filter(has_warehousing=False, is_active=True)
    elif filter == 'inactive':
        clients = clients.filter(is_active=False)
    else:
        clients = clients.filter(is_active=True)

    context = {
        'clients': utils.tree_to_list(clients, sort_by='company_name'),
    }
    return render(request, 'ims/mgmt_customers_list.html', context)
