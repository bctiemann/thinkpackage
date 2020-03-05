# -*- coding: utf-8 -*-


from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Func, F, Count
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden, HttpResponseRedirect, HttpResponseNotFound
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib.auth import (
    login, authenticate, get_user_model, password_validation, update_session_auth_hash,
)

from django_pdfkit import PDFView

from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ims.models import User, Client, Shipment, Transaction, Product, CustContact, Location, Receivable, ShipmentDoc, ClientUser, Pallet, AsyncTask
from ims.forms import AjaxableResponseMixin, UserLoginForm, PasswordChangeForm
from ims import utils

import math
import os
from datetime import datetime, timedelta

import logging
logger = logging.getLogger(__name__)


def home(request):
    context = {
    }
    return render(request, 'home.html', context)


def shipment_doc(request, doc_id=None):
    shipment_doc = get_object_or_404(ShipmentDoc, pk=doc_id)

    if not (request.user.is_admin or request.user.is_authorized_for_client(shipment_doc.shipment.client)):
        raise PermissionDenied

    if not shipment_doc.file:
        raise Http404

    filename = None
    for media_path in [settings.MEDIA_ROOT, settings.MEDIA_ROOT_LEGACY]:
        test_filename = os.path.join(media_path, shipment_doc.file.name)
        if os.path.isfile(test_filename):
            filename = test_filename
    if not filename:
        raise Http404

    logger.info('User {0} downloaded {1}, {2}.{3}'.format(request.user, shipment_doc.id, shipment_doc.basename, shipment_doc.ext))
    with open(filename, 'rb') as file:
        response = HttpResponse(file.read(), content_type=shipment_doc.content_type)
        response['Content-Disposition'] = 'inline;filename={0}.{1}'.format(shipment_doc.basename, shipment_doc.ext)
    return response


def async_task_result(request, async_task_id=None):
    async_task = get_object_or_404(AsyncTask, pk=async_task_id)

    # Pick up here -- add a FileField to AsyncTask instead of url
    if not async_task.result_file:
        raise Http404

    filename = os.path.join(settings.MEDIA_ROOT, async_task.result_file.name)
    if not os.path.isfile(filename):
        raise Http404

    with open(filename, 'rb') as file:
        response = HttpResponse(file.read(), content_type=async_task.result_content_type)
        response['Content-Disposition'] = 'attachment;filename={0}.{1}'.format(async_task.result_basename, async_task.result_extension)
    return response


def pallet_code(request, pallet_id=None):
    pallet = get_object_or_404(Pallet, pallet_id=pallet_id)

#    if not (request.user.is_authenticated):
#        raise PermissionDenied

    response = HttpResponse(content_type='image/png')
    base_image = pallet.get_qrcode(format='PNG')
    base_image.save(response, 'PNG')
    return response


def product_code(request, product_id=None):
    product = get_object_or_404(Product, product_id=product_id)

#    if not (request.user.is_authenticated):
#        raise PermissionDenied

    response = HttpResponse(content_type='image/png')
    base_image = product.get_qrcode(format='PNG')
    base_image.save(response, 'PNG')
    return response


class PalletPrint(PDFView):
    template_name = 'warehouse/pallet_label.html'

    def get(self, *args, **kwargs):
        try:
            return super(PalletPrint, self).get(*args, **kwargs)
        except FileNotFoundError as e:
            logger.warning(e)
            return HttpResponseNotFound('Document not found.')
        except Exception as e:
            logger.warning(e)
            logger.warning('PDF generation failed; retrying')
            return self.get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        pallet = get_object_or_404(Pallet, pk=self.kwargs['pallet_id'])
        pallet.create_qrcode()
        context = super(PalletPrint, self).get_context_data(**kwargs)
        context['pallet'] = pallet
        context['site_url'] = settings.SERVER_BASE_URL
        context['media_url'] = settings.MEDIA_URL
        context['copies'] = list(range(2))
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


class ProductPrint(PDFView):
    template_name = 'warehouse/product_label.html'

    def get(self, *args, **kwargs):
        try:
            return super(ProductPrint, self).get(*args, **kwargs)
        except FileNotFoundError as e:
            logger.warning(e)
            return HttpResponseNotFound('Document not found.')
        except Exception as e:
            logger.warning(e)
            logger.warning('PDF generation failed; retrying')
            return self.get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        product = get_object_or_404(Product, pk=self.kwargs['product_id'])
        product.create_qrcode()
        context = super(ProductPrint, self).get_context_data(**kwargs)
        context['product'] = product
        context['last_received'] = Receivable.objects.filter(transaction__product=product).order_by('-date_created').first()
        context['site_url'] = settings.SERVER_BASE_URL
        context['media_url'] = settings.MEDIA_URL
#        context['copies'] = range(2)
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


class LoginView(LoginView):

    home_url = reverse_lazy('home')
    template_name = 'login.html'
    form_list = (
        ('auth', UserLoginForm),
        ('token', AuthenticationTokenForm),
        ('backup', BackupTokenForm),
    )

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(self.home_url)
        return super(LoginView, self).dispatch(request, *args, **kwargs)


class PasswordChangeView(UpdateView):
    model = User
    form_class = PasswordChangeForm
    template_name = 'accounts/change_password.html'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, self.request.user)
        return response

    def get_success_url(self):
        return reverse_lazy('change-password-done')


class PasswordChangeDoneView(TemplateView):
    template_name = 'accounts/change_password_done.html'