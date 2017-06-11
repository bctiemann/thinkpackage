# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from django.db.models import Sum
from django.contrib.auth import authenticate, login

from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from ims.models import Product, Transaction, Shipment, Client, ClientUser, Location, ShipperAddress
from ims.forms import AjaxableResponseMixin, UserLoginForm, ShipmentForm
from ims import utils

from datetime import datetime, timedelta
import json
import re

import logging
logger = logging.getLogger(__name__)


company_info = {
    'name': settings.COMPANY_NAME,
    'site_email': settings.SITE_EMAIL,
    'phone_number': settings.COMPANY_PHONE_NUMBER,
}


class LoginView(LoginView):
    template_name = 'warehouse/login.html'
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


def home(request):
    return redirect('warehouse-shipments')


def warehouse_shipments(request):

    context = {
    }
    return render(request, 'warehouse/shipments.html', context)


def warehouse_shipments_list(request):

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
    return render(request, 'warehouse/shipments_list.html', context)


def warehouse_shipment_details(request, shipment_id):
    shipment = get_object_or_404(Shipment, pk=shipment_id)

    context = {
        'shipment': shipment,
        'shipper_addresses': ShipperAddress.objects.all(),
    }
    return render(request, 'warehouse/shipment_details.html', context)


def warehouse_receivables(request):

    context = {
    }
    return render(request, 'warehouse/receivables.html', context)


def warehouse_pallets(request):

    context = {
    }
    return render(request, 'warehouse/pallets.html', context)


class ShipmentUpdate(AjaxableResponseMixin, UpdateView):
    model = Shipment
    form_class = ShipmentForm
    template_name = 'warehouse/shipment_details.html'

    def get_object(self):
        return get_object_or_404(Shipment, pk=self.kwargs['shipment_id'])

    def form_valid(self, form):
#        self.object.custcontact_set.update(is_primary=False)
#        if form.cleaned_data['primary_contact']:
#            CustContact.objects.filter(pk=form.cleaned_data['primary_contact']).update(is_primary=True)
        return super(ShipmentUpdate, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super(ShipmentUpdate, self).get_context_data(*args, **kwargs)
#        context['primary_contact'] = self.object.custcontact_set.filter(is_primary=True).first()
        return context

