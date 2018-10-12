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
        shipped_filter = int(request.GET.get('shipped_filter', 1))
    except:
        shipped_filter = 1

    shipments = Shipment.objects.all().order_by('status', '-date_created')

    three_weeks_ago = timezone.now() - timedelta(days=21)

    if shipped_filter:
        shipments = shipments.exclude(status=2)
    else:
        shipments = shipments.filter(status=2, date_shipped__gt=three_weeks_ago)

    context = {
        'shipments': shipments,
        'shipped_filter': shipped_filter,
    }
    return render(request, 'accounting/shipments_list.html', context)

