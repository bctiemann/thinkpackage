# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from django.db.models import Sum, Q
from django.contrib.auth import authenticate, login

from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from ims.models import Product, Transaction, Receivable, Shipment, ShipmentDoc, Client, ClientUser, Location, ReturnedProduct, Pallet
from ims.forms import AjaxableResponseMixin, UserLoginForm
from warehouse_app import forms
from ims import utils

from datetime import datetime, timedelta
import json
import re

import logging
logger = logging.getLogger(__name__)


class LoginView(LoginView):
    template_name = 'warehouse_app/login.html'
    form_list = (
        ('auth', UserLoginForm),
        ('token', AuthenticationTokenForm),
        ('backup', BackupTokenForm),
    )


def home(request):

    context = {
    }
    return render(request, 'warehouse_app/home.html', context)


def menu(request):

    context = {
    }
    return render(request, 'warehouse_app/menu.html', context)


def receive(request):

    context = {
        'receivables': Transaction.objects.filter(receivable__isnull=False, cases__isnull=True).order_by('date_created'),
    }
    return render(request, 'warehouse_app/receive.html', context)


def receive_form(request, receivable_id):

    logger.info(request.resolver_match.app_name)
    receivable = get_object_or_404(Receivable, pk=receivable_id)

    context = {
        'receivable': receivable
    }
    return render(request, 'warehouse_app/receive_form.html', context)


def pallet(request):

    context = {
        'shipments': Shipment.objects.filter(status=0).order_by('location__zip', '-date_created')
    }
    return render(request, 'warehouse_app/pallet.html', context)


def check_pallet_contents(request):

    context = {
    }
    return render(request, 'warehouse_app/check_pallet_contents.html', context)


def check_product(request):

    context = {
    }
    return render(request, 'warehouse_app/check_product.html', context)


def barcode_lookup_product(request):

    context = {
    }
    return render(request, 'warehouse_app/lookup_product.html', context)


def barcode_lookup_pallet_contents(request):

    code = request.GET.get('c')
    if code.upper().startswith('1TP:'):
        try:
            pallet = Pallet.objects.get(pallet_id=code[4:])
        except Pallet.DoesNotExist:
            pallet = None
            pallet = Pallet.objects.get(pk=7704)

    context = {
        'pallet': pallet,
    }
    return render(request, 'warehouse_app/lookup_pallet_contents.html', context)


def barcode_pallet(request):
    response = {}

    return JsonResponse({})


class PalletCreate(AjaxableResponseMixin, CreateView):
    model = Pallet
    form_class = forms.PalletCreateForm
    template_name = 'warehouse_app/pallet.html'

    def form_valid(self, form):
        data = {
            'success': True,
        }
        logger.warning(form.data)
        logger.warning(form.cleaned_data)

        pallet = form.save(commit=False)
        pallet.client = pallet.shipment.client
        pallet.save()

        return JsonResponse(data)

