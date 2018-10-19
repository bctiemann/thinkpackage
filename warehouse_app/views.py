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

from ims.models import Product, Transaction, Receivable, Shipment, ShipmentDoc, Client, ClientUser, Location, ReturnedProduct, Pallet, PalletContents
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

    code = request.GET.get('c')
    if code.upper().startswith('1TP:'):
        try:
            product = Product.objects.get(product_id=code[4:])
        except Product.DoesNotExist:
            product = None

    context = {
        'product': product,
    }
    return render(request, 'warehouse_app/lookup_product.html', context)


def barcode_lookup_pallet_contents(request):

    code = request.GET.get('c')
    if code.upper().startswith('1TP:'):
        try:
            pallet = Pallet.objects.get(pallet_id=code[4:])
        except Pallet.DoesNotExist:
            pallet = None

    context = {
        'pallet': pallet,
    }
    return render(request, 'warehouse_app/lookup_pallet_contents.html', context)


def barcode_pallet(request):
    response = {}

    code = request.GET.get('c')
    if code.upper().startswith('1TP:'):
        try:
            product = Product.objects.get(product_id=code[4:])
            response['id'] = product.id
            response['product_id'] = product.product_id
            response['product_name'] = product.name
            response['company_name'] = product.client.company_name
        except Product.DoesNotExist:
            product = None

    return JsonResponse(response)


class PalletCreate(AjaxableResponseMixin, CreateView):
    model = Pallet
    form_class = forms.PalletCreateForm
    template_name = 'warehouse_app/pallet.html'

    def form_valid(self, form):
        data = {
            'success': False,
        }

        products = form.data.get('products')
        if not products:
            data['error'] = 'No products scanned; pallet not built.'
            return JsonResponse(data)

        pallet = form.save(commit=False)
        if pallet.shipment:
            pallet.client = pallet.shipment.client
        pallet.save()

        for product_data in products.split(','):
            product_id, cases = product_data.split(':')
            try:
                product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                continue
            PalletContents.objects.create(
                pallet = pallet,
                product = product,
                cases = cases,
            )

            if pallet.shipment:
                product_transaction = Transaction.objects.get(shipment=pallet.shipment, product=product)

                if product_transaction.cases > cases:
                    pass
                    # Create new shipment with same client, PO, SO, location
                    # Create new transaction with cases = product_transaction.cases - cases

                product_transaction.cases = cases
                product_transaction.cases_remaining = product.cases_available
                product_transaction.save()

        if pallet.shipment:
            pass
            # Check for any transactions in this shipment with is_scanned_to_pallet = False
            # If none, set shipment status=1

        data['success'] = True
        return JsonResponse(data)

