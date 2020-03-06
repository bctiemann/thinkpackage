# -*- coding: utf-8 -*-


from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden, HttpResponseBadRequest
from django.db.models import Sum, Q
from django.contrib.auth import authenticate, login

#from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
#from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from ims.models import Product, Transaction, Shipment, ShipmentDoc, Client, ClientUser, Location, ReturnedProduct
from ims.forms import AjaxableResponseMixin, UserLoginForm
from ims.views import LoginView
from accounting import forms
from ims import utils

from datetime import datetime, timedelta
import json
import re

import logging
logger = logging.getLogger(__name__)


class LoginView(LoginView):
    template_name = 'accounting/login.html'
    home_url = reverse_lazy('accounting:home')
#    form_list = (
#        ('auth', UserLoginForm),
#        ('token', AuthenticationTokenForm),
#        ('backup', BackupTokenForm),
#    )

def home(request):
    return redirect('accounting:shipments')


def shipments(request):
    logger.info(f'{request.user} viewed accounting shipments page')
    #    locations = Location.objects.filter(client__in=[c['obj'] for c in request.selected_client.children], is_active=True).order_by('name')

    context = {
    }
    return render(request, 'accounting/shipments.html', context)


def shipments_list(request):

    try:
        status_filter = int(request.GET.get('status_filter', 1))
    except:
        status_filter = 1

    context = {
        'status_filter': status_filter,
    }
    return render(request, 'accounting/shipments_list.html', context)


def shipments_fetch(request):

    try:
        status_filter = int(request.GET.get('status_filter', 1))
    except:
        status_filter = 1

    page_size = settings.INFINITE_SCROLL_PAGE_SIZE
    start = int(request.GET.get('start', 0))
    end = start + page_size

    shipments = Shipment.objects.all()
    shipments = shipments.filter(
        Q(transaction__product__accounting_prepay_type=Product.AccountingPrepayType.INVQ) | Q(delivery_charge__gt=0),
        status=Shipment.Status.SHIPPED,
        accounting_status=status_filter
    )\
    .filter(location__isnull=False)
    shipments = shipments.distinct().order_by('-id', '-date_created', '-invoice_number')

    # three_months_ago = timezone.now() - timedelta(days=90)

    # if status_filter == 2:
    #     shipments = shipments.filter(date_shipped__gt=three_months_ago)
#    else:
#        shipments = shipments.filter(status=2, date_shipped__gt=three_weeks_ago)

    context = {
        'shipments': shipments[start:end],
        'status_filter': status_filter,
    }
    return render(request, 'accounting/shipments_list_shipments.html', context)


def shipment_details(request, shipment_id):
    shipment = get_object_or_404(Shipment, pk=shipment_id)

    context = {
        'shipment': shipment,
#        'shipper_addresses': ShipperAddress.objects.all(),
    }
    return render(request, 'accounting/shipment_details.html', context)


def reconciliation(request):

    context = {
    }
    return render(request, 'accounting/reconciliation.html', context)


def reconciliation_list(request):

    try:
        completed_filter = int(request.GET.get('completed_filter', 0))
    except:
        completed_filter = 0

    returned_products = ReturnedProduct.objects.all().order_by('-date_returned')

    if completed_filter == 1:
        returned_products = returned_products.filter(date_reconciled__isnull=False)
    else:
        returned_products = returned_products.filter(date_reconciled__isnull=True)

    context = {
        'completed_filter': completed_filter,
        'returned_products': returned_products,
    }
    return render(request, 'accounting/reconciliation_list.html', context)


def incoming(request):

    context = {
    }
    return render(request, 'accounting/incoming.html', context)


class ShipmentUpdateInvoice(AjaxableResponseMixin, UpdateView):
    model = Shipment
    form_class = forms.ShipmentInvoiceForm
    template_name = 'accounting/shipment_details.html'

    def get_object(self):
        return get_object_or_404(Shipment, pk=self.kwargs['shipment_id'])


class ShipmentSubmitInvoice(ShipmentUpdateInvoice):
    form_class = forms.ShipmentSubmitInvoiceForm


class ReturnedProductReconcile(AjaxableResponseMixin, UpdateView):
    model = ReturnedProduct
    form_class = forms.ReconciliationForm
    template_name = 'accounting/reconciliation.html'

    def get_object(self):
        return get_object_or_404(ReturnedProduct, pk=self.kwargs['returned_product_id'])

    def form_valid(self, form):
        self.object.date_reconciled = timezone.now()
        return super(ReturnedProductReconcile, self).form_valid(form)


class ShipmentDocCreate(AjaxableResponseMixin, CreateView):
    model = ShipmentDoc
    form_class = forms.ShipmentDocForm
    template_name = 'warehouse/shipment_docs.html'

    def form_valid(self, form):
        logger.warning(form.data)
        logger.warning(self.request.FILES)
        if not 'file' in self.request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file was uploaded.',
            })
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

