# -*- coding: utf-8 -*-


from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from django.db.models import Sum, Count
from django.contrib.auth import authenticate, login

from rest_framework.views import APIView
from rest_framework.response import Response

from django_pdfkit import PDFView

#from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
#from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from ims.models import Product, Transaction, Shipment, Client, ClientUser, Location, ShipperAddress, Pallet, ShipmentDoc, ActionLog
from ims.forms import AjaxableResponseMixin, UserLoginForm
from ims.views import LoginView, AbstractPDFView
from ims.tasks import email_purchase_order
from ims.sps import SPSService
from warehouse import forms
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
    home_url = reverse_lazy('warehouse:home')
#    form_list = (
#        ('auth', UserLoginForm),
#        ('token', AuthenticationTokenForm),
#        ('backup', BackupTokenForm),
#    )


#class PhoneSetupView(PhoneSetupView):
#    success_url = reverse_lazy('two_factor:profile')


#class PhoneDeleteView(PhoneDeleteView):
#    success_url = reverse_lazy('two_factor:profile')


#class DisableView(DisableView):
#    success_url = reverse_lazy('two_factor:profile')


def home(request):
    return redirect('warehouse:shipments')


def shipments(request):
    logger.info(f'{request.user} viewed warehouse shipments page')

    context = {
    }
    return render(request, 'warehouse/shipments.html', context)


def shipments_list(request):

    try:
        shipped_filter = int(request.GET.get('shipped_filter', 1))
    except:
        shipped_filter = 1

    context = {
        'shipped_filter': shipped_filter,
    }
    return render(request, 'warehouse/shipments_list.html', context)


def shipments_fetch(request):

    try:
        shipped_filter = int(request.GET.get('shipped_filter', 1))
    except:
        shipped_filter = 1

    page_size = settings.INFINITE_SCROLL_PAGE_SIZE
    start = int(request.GET.get('start', 0))
    end = start + page_size

    shipments = Shipment.objects.all().order_by('status', '-date_created')

    # three_weeks_ago = timezone.now() - timedelta(days=21)

    shipment_id = request.GET.get('shipment_id')
    if shipment_id and shipment_id.isnumeric():
        shipments = shipments.filter(pk=int(shipment_id))

    if shipped_filter:
        shipments = shipments.exclude(status=Shipment.Status.SHIPPED)
    else:
        # shipments = shipments.filter(status=2, date_shipped__gt=three_weeks_ago)
        shipments = shipments.filter(status=Shipment.Status.SHIPPED)[start:end]

    context = {
        'shipments': shipments,
        'shipped_filter': shipped_filter,
    }
    return render(request, 'warehouse/shipments_list_shipments.html', context)


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

    context = {
        'received_filter': received_filter,
    }
    return render(request, 'warehouse/receivables_list.html', context)


def receivables_fetch(request):

    try:
        received_filter = int(request.GET.get('received_filter', 1))
    except:
        received_filter = 1

    page_size = settings.INFINITE_SCROLL_PAGE_SIZE
    start = int(request.GET.get('start', 0))
    end = start + page_size

    transactions = Transaction.objects.filter(receivable__isnull=False).annotate(null_count=Count('cases')).order_by('-null_count', '-receivable__date_created')

    # three_weeks_ago = timezone.now() - timedelta(days=21)

    receivable_id = request.GET.get('receivable_id')
    if receivable_id and receivable_id.isnumeric():
        transactions = transactions.filter(receivable__pk=int(receivable_id))

    if received_filter:
        transactions = transactions.filter(cases__isnull=True)[start:end]
    else:
        # transactions = transactions.filter(cases__isnull=False, receivable__date_created__gt=three_weeks_ago)
        transactions = transactions.filter(cases__isnull=False)[start:end]

    context = {
        'transactions': transactions,
        'received_filter': received_filter,
    }
    return render(request, 'warehouse/receivables_list_receivables.html', context)


def pallets(request):

    context = {
        'pallets': Pallet.objects.filter(shipment__isnull=True, client__isnull=True).order_by('-date_created'),
    }
    return render(request, 'warehouse/pallets.html', context)


class ShipmentUpdate(AjaxableResponseMixin, UpdateView):
    model = Shipment
    form_class = forms.ShipmentForm
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
        self.object.status = Shipment.Status.SHIPPED
        self.object.save()
        for transaction in self.object.transaction_set.all():
            ActionLog.objects.create(
                user = self.request.user,
                client = self.object.client,
                product = transaction.product,
                log_message = 'Shipment {0} shipped. {1} cases deducted'.format(self.object.id, transaction.cases),
                app = self.request.resolver_match.app_name,
            )

            transaction.product.cases_inventory_orig = transaction.product.cases_inventory
            transaction.product.cases_inventory -= transaction.cases
            if transaction.product.cases_inventory < 0:
                logger.warning('Shipment {0}: {1} cases deducted from product {2}, greater than {3} cases in stock'.format(self.object.id, transaction.cases, transaction.product.id, transaction.product.cases_inventory_orig))
                transaction.product.cases_inventory = 0
#            transaction.product.units_inventory = transaction.product.cases_inventory * transaction.product.packing
            transaction.product.save()

        # Moved this PO email generation to the client's placement of the order
        # if self.object.transaction_set.filter(product__accounting_prepay_type=Product.AccountingPrepayType.INVQ).exists():
        #     request_dict = {
        #         'scheme': self.request.scheme,
        #         'host': self.request.get_host(),
        #     }
        #     email_purchase_order(request=request_dict, shipment_id=self.object.id)

        # Submit shipment payload to SPS
        if settings.SPS_ENABLE:
            sps = SPSService()
            sps.submit_shipment(self.object)

        logger.info(f'{self.request.user} shipped shipment {self.object}')
        return response

    def get_object(self):
        return get_object_or_404(Shipment, pk=self.kwargs['shipment_id'])


class PalletUpdate(AjaxableResponseMixin, UpdateView):
    model = Pallet
    form_class = forms.PalletForm
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


#class BillOfLadingView(TemplateView):
class BillOfLadingView(AbstractPDFView):
    template_name = 'warehouse/bill_of_lading.html'
    max_products_per_page = 20

    def get_context_data(self, **kwargs):
        context = super(BillOfLadingView, self).get_context_data(**kwargs)
        shipment = get_object_or_404(Shipment, pk=self.kwargs['shipment_id'])
        context['shipment'] = shipment
        context['total_pages'] = int(math.ceil(float(shipment.transaction_set.count()) / float(self.max_products_per_page)))
        context['pages'] = list(range(context['total_pages']))
        context['max_products_per_page'] = self.max_products_per_page
        context['remainder_rows'] = list(range(self.max_products_per_page - (shipment.transaction_set.count() % self.max_products_per_page)))
        logger.info(f'{self.request.user} generated Bill of Lading for shipment {shipment.id} ({shipment.client})')
        return context


class PurchaseOrderView(AbstractPDFView):
    template_name = 'warehouse/purchase_order.html'
    max_products_per_page = 20

    def get_context_data(self, **kwargs):
        context = super(PurchaseOrderView, self).get_context_data(**kwargs)
        shipment = get_object_or_404(Shipment, pk=self.kwargs['shipment_id'])
        context['shipment'] = shipment
        context['invq_transactions'] = shipment.transaction_set.filter(product__accounting_prepay_type=Product.AccountingPrepayType.INVQ)
        context['total_pages'] = int(math.ceil(float(shipment.transaction_set.count()) / float(self.max_products_per_page)))
        context['pages'] = list(range(context['total_pages']))
        context['max_products_per_page'] = self.max_products_per_page
        context['remainder_rows'] = list(range(self.max_products_per_page - (shipment.transaction_set.count() % self.max_products_per_page)))
        return context


class SendPurchaseOrder(APIView):

    def post(self, request, shipment_id):
        shipment = get_object_or_404(Shipment, pk=shipment_id)

        request_dict = {
            'scheme': self.request.scheme,
            'host': self.request.get_host(),
        }
        email_purchase_order(request=request_dict, shipment_id=shipment.id)

        return Response({'success': True})