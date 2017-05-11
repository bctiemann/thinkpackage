# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect


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
