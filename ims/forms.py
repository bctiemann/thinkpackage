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


ENABLED_CHOICES = (
    (True, 'Enabled'),
    (False, 'Disabled'),
)

WAREHOUSING_CHOICES = (
    (True, 'Warehousing required'),
    (False, 'No warehousing required'),
)

DOMESTIC_CHOICES = (
    (False, 'Import (12-14 wks)'),
    (True, 'Domestic (6-8 wks)'),
)


class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def form_invalid(self, form):
        logger.warning(form.errors)
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return HttpResponse(form.errors.as_json())
#            return HttpResponse(form.errors.as_json(), content_type='application/json')
        else:
            return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {
                'success': True,
                'pk': self.object.pk,
            }
            return JsonResponse(data)
        else:
            return response


class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Login (email)'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    # class Meta:
        # widgets = {
            # 'username': forms.EmailInput(attrs={'placeholder': 'Login'}),
            # 'password': forms.PasswordInput(attrs={'placeholder': 'Password'}),
        # }


