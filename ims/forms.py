from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import SetPasswordForm, PasswordResetForm, AuthenticationForm
from django.contrib.auth import (
    login, authenticate, get_user_model, password_validation, update_session_auth_hash,
)
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from django.utils.translation import gettext, gettext_lazy as _

from localflavor.us.forms import USStateField, USZipCodeField
from localflavor.us.us_states import STATE_CHOICES

from ims.models import User, Client, CustContact, Location, Product, Receivable, Transaction, ShipmentDoc, Shipment, Pallet, ReturnedProduct
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
        logger.warning(form.errors.as_json())
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


class PasswordChangeForm(SetPasswordForm):
    current_password = forms.CharField(
        label=_("Current password"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        super().__init__(self.instance, *args, **kwargs)
        self.fields['new_password2'].label = 'Repeat password'
        self.error_messages['incorrect_current_password'] = 'Current password is incorrect.'
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        current_password_correct = authenticate(username=self.instance.email, password=current_password)
        if not current_password_correct:
            raise forms.ValidationError(
                self.error_messages['incorrect_current_password'],
                code='incorrect_current_password',
            )
        return current_password