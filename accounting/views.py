# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from django.db.models import Sum, Q
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


class LoginView(LoginView):
    template_name = 'accounting/login.html'
    form_list = (
        ('auth', UserLoginForm),
        ('token', AuthenticationTokenForm),
        ('backup', BackupTokenForm),
    )

def home(request):
    return redirect('accounting:shipments')


def accounting_shipments(request):
#    locations = Location.objects.filter(client__in=[c['obj'] for c in request.selected_client.children], is_active=True).order_by('name')

    context = {
    }
    return render(request, 'accounting/shipments.html', context)


def accounting_shipments_list(request):

    try:
        status_filter = int(request.GET.get('status_filter', 1))
    except:
        status_filter = 1

    shipments = Shipment.objects.filter(Q(transaction__product__account_prepay_type=1) | Q(delivery_charge__gt=0), status=2).order_by('-date_created', '-invoice_number')

    three_months_ago = timezone.now() - timedelta(days=90)

    if status_filter == 2:
        shipments = shipments.filter(date_shipped__gt=three_months_ago)
#    else:
#        shipments = shipments.filter(status=2, date_shipped__gt=three_weeks_ago)

    context = {
        'shipments': shipments[0:100],
        'status_filter': status_filter,
    }
    return render(request, 'accounting/shipments_list.html', context)


def accounting_reconciliation(request):

    context = {
    }
    return render(request, 'accounting/reconciliation.html', context)


def accounting_reconciliation_list(request):

    context = {
    }
    return render(request, 'accounting/reconciliation_list.html', context)


def accounting_incoming(request):

    context = {
    }
    return render(request, 'accounting/incoming.html', context)
