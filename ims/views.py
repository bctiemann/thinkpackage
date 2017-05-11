# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect

from ims.models import Client
from ims import utils


def home(request):
    context = {
    }
    return render(request, 'ims/home.html', context)

def mgmt(request):
    context = {
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
