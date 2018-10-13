# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from django.db.models import Sum, Count
from django.contrib.auth import authenticate, login

from django_pdfkit import PDFView

from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from ims.models import Product, Transaction, Shipment, Client, ClientUser, Location, ShipperAddress, Pallet, ShipmentDoc, ActionLog
from ims.forms import AjaxableResponseMixin, UserLoginForm, ShipmentForm, PalletForm, ShipmentDocForm
from ims import utils

from datetime import datetime, timedelta
import json
import re
import math

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


#class PhoneSetupView(PhoneSetupView):
#    success_url = reverse_lazy('two_factor:profile')


#class PhoneDeleteView(PhoneDeleteView):
#    success_url = reverse_lazy('two_factor:profile')


#class DisableView(DisableView):
#    success_url = reverse_lazy('two_factor:profile')


def home(request):
    return redirect('warehouse:shipments')


def shipments(request):

    context = {
    }
    return render(request, 'warehouse/shipments.html', context)


def shipments_list(request):

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


def shipment_details(request, shipment_id):
    shipment = get_object_or_404(Shipment, pk=shipment_id)

    context = {
        'shipment': shipment,
        'shipper_addresses': ShipperAddress.objects.all(),
    }
    return render(request, 'warehouse/shipment_details.html', context)


def receivables(request):

    context = {
    }
    return render(request, 'warehouse/receivables.html', context)


def receivables_list(request):

    try:
        received_filter = int(request.GET.get('received_filter', 1))
    except:
        received_filter = 1

    transactions = Transaction.objects.filter(receivable__isnull=False).annotate(null_count=Count('cases')).order_by('-null_count', '-receivable__date_created')

    three_weeks_ago = timezone.now() - timedelta(days=21)

    if received_filter:
        transactions = transactions.filter(cases__isnull=True)
    else:
        transactions = transactions.filter(cases__isnull=False, receivable__date_created__gt=three_weeks_ago)

    context = {
        'transactions': transactions,
        'received_filter': received_filter,
    }
    return render(request, 'warehouse/receivables_list.html', context)


def pallets(request):

    context = {
        'pallets': Pallet.objects.filter(shipment__isnull=True, client__isnull=True).order_by('-date_created'),
    }
    return render(request, 'warehouse/pallets.html', context)


class ShipmentUpdate(AjaxableResponseMixin, UpdateView):
    model = Shipment
    form_class = ShipmentForm
    template_name = 'warehouse/shipment_details.html'

    def get_object(self):
        return get_object_or_404(Shipment, pk=self.kwargs['shipment_id'])


class ShipmentShip(AjaxableResponseMixin, UpdateView):
    model = Shipment
    template_name = 'warehouse/shipment_details.html'
    fields = ['delivery_charge',]

    def form_valid(self, form):
        response = super(ShipmentShip, self).form_valid(form)
        self.object.date_shipped = timezone.now()
        self.object.status = 2
        self.object.save()
        for transaction in self.object.transaction_set.all():
            ActionLog.objects.create(
                user = self.request.user,
                client = self.object.client,
                product = self.object,
                log_message = 'Shipment {0} shipped. {1} cases deducted'.format(self.object.id, transaction.cases),
                app = 'warehouse',
            )

            transaction.product.cases_inventory_orig = transaction.product.cases_inventory
            transaction.product.cases_inventory -= transaction.cases
            if transaction.product.cases_inventory < 0:
                logger.warning('Shipment {0}: {1} cases deducted from product {2}, greater than {3} cases in stock'.format(self.object.id, transaction.cases, transaction.product.cases_inventory_orig))
                transaction.product.cases_inventory = 0
#            transaction.product.units_inventory = transaction.product.cases_inventory * transaction.product.packing
            transaction.product.save()

        return response

    def get_object(self):
        return get_object_or_404(Shipment, pk=self.kwargs['shipment_id'])


class PalletUpdate(AjaxableResponseMixin, UpdateView):
    model = Pallet
    form_class = PalletForm
    template_name = 'warehouse/pallet_details.html'

    def get_object(self):
        return get_object_or_404(Pallet, pk=self.kwargs['pallet_id'])


class PalletDelete(AjaxableResponseMixin, DeleteView):
    model = Pallet

    def get_object(self):
        return get_object_or_404(Pallet, pk=self.kwargs['pallet_id'])

    def get_success_url(self):
        return reverse_lazy('warehouse:pallets')

    def post(self, *args, **kwargs):
        super(PalletDelete, self).post(*args, **kwargs)
        return JsonResponse({'success': True})


#class PalletPrint(TemplateView):
class PalletPrint(PDFView):
    template_name = 'warehouse/pallet_label.html'

    def get(self, *args, **kwargs):
        try:
            return super(PalletPrint, self).get(*args, **kwargs)
        except:
            logger.warning('PDF generation failed; retrying')
            return self.get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        pallet = get_object_or_404(Pallet, pk=self.kwargs['pallet_id'])
        pallet.create_qrcode()
        context = super(PalletPrint, self).get_context_data(**kwargs)
        context['pallet'] = pallet
        context['site_url'] = settings.SERVER_BASE_URL
        context['media_url'] = settings.MEDIA_URL
        return context

    def get_pdfkit_options(self):
        options = {
            'page-size': 'Letter',
            'margin-top': '0.52in',
            'margin-right': '0.25in',
            'margin-bottom': '0.0in',
            'margin-left': '0.25in',
            'encoding': "UTF-8",
            'no-outline': None,
        }
        return options


class ShipmentDocCreate(AjaxableResponseMixin, CreateView):
    model = ShipmentDoc
    form_class = ShipmentDocForm
    template_name = 'warehouse/shipment_docs.html'

    def form_valid(self, form):
        logger.warning(form.data)
        logger.warning(self.request.FILES)
        response = super(ShipmentDocCreate, self).form_valid(form)
        uploaded_file = self.request.FILES['file']
        self.object.content_type = uploaded_file.content_type
        self.object.size = uploaded_file.size
        filename_parts = uploaded_file.name.split('.')
        self.object.basename = '.'.join(filename_parts[0:-1])
        self.object.ext = filename_parts[-1]
        self.object.save()
        logger.info('ShipmentDoc {0} created.'.format(self.object))
        return response

    def get_context_data(self, *args, **kwargs):
        context = super(ShipmentDocCreate, self).get_context_data(*args, **kwargs)
        shipment = get_object_or_404(Shipment, pk=self.kwargs['shipment_id'])
        context['shipment'] = shipment
        return context


class ShipmentDocDelete(AjaxableResponseMixin, DeleteView):
    model = ShipmentDoc

    def get_object(self):
        return get_object_or_404(ShipmentDoc, pk=self.kwargs['doc_id'])

    def get_success_url(self):
        return reverse_lazy('warehouse:shipment-docs', kwargs={'shipment_id': self.object.shipment.id})

    def post(self, *args, **kwargs):
        super(ShipmentDocDelete, self).post(*args, **kwargs)
        return JsonResponse({'success': True, 'shipment_id': self.object.shipment_id})


#class BillOfLadingView(TemplateView):
class BillOfLadingView(PDFView):
    template_name = 'warehouse/bill_of_lading.html'
    max_products_per_page = 20

    def get_context_data(self, **kwargs):
        context = super(BillOfLadingView, self).get_context_data(**kwargs)
        shipment = get_object_or_404(Shipment, pk=self.kwargs['shipment_id'])
        context['shipment'] = shipment
        context['total_pages'] = int(math.ceil(float(shipment.transaction_set.count()) / float(self.max_products_per_page)))
        context['pages'] = range(context['total_pages'])
        context['max_products_per_page'] = self.max_products_per_page
        context['remainder_rows'] = range(self.max_products_per_page - (shipment.transaction_set.count() % self.max_products_per_page))
        return context

    def get_pdfkit_options(self):
        options = {
            'page-size': 'Letter',
            'margin-top': '0.52in',
            'margin-right': '0.25in',
            'margin-bottom': '0.0in',
            'margin-left': '0.25in',
            'encoding': "UTF-8",
            'no-outline': None,
        }
        return options
