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


class PalletCreateForm(forms.ModelForm):

    class Meta:
        model = Pallet
        fields = ['shipment',]

