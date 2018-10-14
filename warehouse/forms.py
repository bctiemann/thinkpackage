from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden

from localflavor.us.forms import USStateField, USZipCodeField
from localflavor.us.us_states import STATE_CHOICES

from ims.models import Client, CustContact, Location, Product, Receivable, Transaction, ShipmentDoc, Shipment, Pallet, ReturnedProduct
from ims import utils

import logging
logger = logging.getLogger(__name__)


class ShipmentDocForm(forms.ModelForm):
    class Meta:
        model = ShipmentDoc
        fields = ['shipment', 'file']


class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = [
            'shipper_address',
            'carrier',
            'pro_number',
            'purchase_order_number',
            'third_party',
            'shipment_class',
            'pallet_count',
            'date_shipped',
            'shipper_instructions',
            'consignee_instructions',
            'inside_delivery',
            'liftgate_required',
            'appointment_required',
            'sort_segregation',
        ]
        widgets = {
            'shipper_address': forms.Select(attrs={'style': 'margin: 10px 0px;'}),
            'date_shipped': forms.DateInput(format='%m/%d/%Y'),
        }


class PalletForm(forms.ModelForm):
    class Meta:
        model = Pallet
        fields = ['shipment',]

