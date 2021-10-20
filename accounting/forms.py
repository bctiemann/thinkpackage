from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden

from localflavor.us.forms import USStateField, USZipCodeField
from localflavor.us.us_states import STATE_CHOICES

from ims.models import Client, Location, Product, Receivable, Transaction, ShipmentDoc, Shipment, Pallet, ReturnedProduct
from ims import utils

import logging
logger = logging.getLogger(__name__)


class ShipmentInvoiceForm(forms.ModelForm):
    invoice_number = forms.IntegerField(required=True)

    class Meta:
        model = Shipment
        fields = ['invoice_number', 'accounting_status']


class ShipmentSubmitInvoiceForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ['accounting_status']


class ReconciliationForm(forms.ModelForm):
    class Meta:
        model = ReturnedProduct
        fields = []
