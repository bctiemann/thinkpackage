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
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.contrib.auth import (
    login, authenticate, get_user_model, password_validation, update_session_auth_hash, logout as auth_logout,
)
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, LogoutView, INTERNAL_RESET_SESSION_TOKEN

from ims.pdf import PDFView

from two_factor.views import LoginView, DisableView
from two_factor.plugins.phonenumber.views import PhoneSetupView, PhoneDeleteView
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ims.models import User, Client, Shipment, Transaction, Product, Location, Receivable, ShipmentDoc, ClientUser, Pallet, AsyncTask, ActionLog
from ims.forms import AjaxableResponseMixin, UserLoginForm, PasswordChangeForm, ShipmentDocForm
from ims import utils

import math
import os
from datetime import datetime, timedelta

import logging
logger = logging.getLogger(__name__)
auth_logger = logging.getLogger('auth')


def home(request):
    context = {
    }
    return render(request, 'home.html', context)


def csrf_failure(request, reason=''):
    context = {'reason': reason}
    return render(request, 'csrf_failure.html', context)


def shipment_doc(request, doc_id=None):
    shipment_doc = get_object_or_404(ShipmentDoc, pk=doc_id)

    if not request.user.is_authenticated or not (
        request.user.is_authorized_for_docs or (
            shipment_doc.shipment.client and request.user.is_authorized_for_client(shipment_doc.shipment.client)
        )
    ):
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
        response['Content-Disposition'] = 'inline;filename={0}'.format(shipment_doc.clean_filename)
    return response


def async_task_result(request, async_task_id=None):
    async_task = get_object_or_404(AsyncTask, pk=async_task_id)

    if not request.user.is_admin:
        raise PermissionDenied

    # Pick up here -- add a FileField to AsyncTask instead of url
    if not async_task.result_file:
        raise Http404

    filename = os.path.join(settings.MEDIA_ROOT, async_task.result_file.name)
    if not os.path.isfile(filename):
        raise Http404

    with open(filename, 'rb') as file:
        response = HttpResponse(file.read(), content_type=async_task.result_content_type)
        response['Content-Disposition'] = 'attachment;filename={0}'.format(async_task.result_filename)
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


class AbstractPDFView(PDFView):

    def get(self, *args, **kwargs):
        try:
            return super().get(*args, **kwargs)
        except FileNotFoundError as e:
            logger.warning(e)
            return HttpResponseNotFound('Document not found.')
        except Exception as e:
            logger.warning(e)
            logger.warning('PDF generation failed; retrying')
            return self.get(*args, **kwargs)

    def get_pdfkit_options(self):
        options = {
            'quiet': '',
            'page-size': 'Letter',
            'margin-top': '0.52in',
            'margin-right': '0.25in',
            'margin-bottom': '0.0in',
            'margin-left': '0.25in',
            'encoding': "UTF-8",
            'no-outline': None,
        }
        return options


class PalletPrint(AbstractPDFView):
    template_name = 'warehouse/pallet_label.html'

    def get_context_data(self, **kwargs):
        pallet = get_object_or_404(Pallet, pk=self.kwargs['pallet_id'])
        if settings.GENERATE_QRCODE_IMAGES:
            pallet.create_qrcode()
        context = super(PalletPrint, self).get_context_data(**kwargs)
        context['pallet'] = pallet
        context['site_url'] = settings.SERVER_BASE_URL
        context['media_url'] = settings.MEDIA_URL
        context['copies'] = list(range(2))
        logger.info(f'{self.request.user} generated printable labels for pallet {pallet.pallet_id} ({pallet.client})')
        return context


class ProductPrint(AbstractPDFView):
    template_name = 'warehouse/product_label.html'

    def get_context_data(self, **kwargs):
        product = get_object_or_404(Product, pk=self.kwargs['product_id'])
        if settings.GENERATE_QRCODE_IMAGES:
            product.create_qrcode()
        context = super(ProductPrint, self).get_context_data(**kwargs)
        context['product'] = product
        context['last_received'] = Receivable.objects.filter(transaction__product=product).order_by('-date_created').first()
        context['site_url'] = settings.SERVER_BASE_URL
        context['media_url'] = settings.MEDIA_URL
#        context['copies'] = range(2)
        logger.info(f'{self.request.user} generated printable labels for product {product} ({product.client})')
        return context


class ShipmentDocCreate(AjaxableResponseMixin, CreateView):
    model = ShipmentDoc
    form_class = ShipmentDocForm
    template_name = 'mgmt/shipment_docs.html'

    def form_valid(self, form):
        logger.info(form.data)
        logger.info(self.request.FILES)
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
        if len(filename_parts) == 1:
            filename_parts.append('')
        self.object.basename = '.'.join(filename_parts[0:-1])
        self.object.ext = filename_parts[-1]
        self.object.save()
        logger.info(
            f'{self.request.user} created shipment doc {self.object.id} {self.object} for shipment {self.object.shipment} ({self.object.shipment.client})')
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

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        logger.info(
            f'{request.user} deleted shipment doc {self.object.id} {self.object} for shipment {self.object.shipment}')
        ActionLog.objects.create(
            user=self.request.user,
            client=self.object.shipment.client,
            product=None,
            log_message=f'Deleted shipment doc {self.object} for shipment {self.object.shipment}',
            app=self.request.resolver_match.app_name,
        )
        self.object.delete()

    def get_success_url(self):
        return reverse_lazy('mgmt:shipment-docs', kwargs={'shipment_id': self.object.shipment.id})

    def post(self, *args, **kwargs):
        super(ShipmentDocDelete, self).post(*args, **kwargs)
        return JsonResponse({'success': True, 'shipment_id': self.object.shipment_id})


class LoginView(LoginView):

    home_url = reverse_lazy('home')
    template_name = 'login.html'
    form_list = (
        ('auth', UserLoginForm),
        ('token', AuthenticationTokenForm),
        ('backup', BackupTokenForm),
    )

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        logger.info(f'{request.resolver_match.app_name} login: {request.user} {request.method} '
                    f'{request.POST.get("auth-username")} {request.META.get("HTTP_X_FORWARDED_FOR")} '
                    f'{request.POST.get("csrfmiddlewaretoken")}')
        if settings.LOG_AUTH:
            auth_logger.info(f'{request.user} {request.POST}')
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(self.home_url)
        return super(LoginView, self).dispatch(request, *args, **kwargs)


class LogoutView(LogoutView):

    http_method_names = ["get", "post", "options"]

    def dispatch(self, request, *args, **kwargs):
        logger.info(f'{request.user} logged out.')
        return super().dispatch(request, *args, **kwargs)

    # TODO: Make this a POST from all templates and eliminate this method
    def get(self, request, *args, **kwargs):
        """Logout may be done via POST."""
        auth_logout(request)
        redirect_to = self.get_success_url()
        if redirect_to != request.get_full_path():
            # Redirect to target page once the session has been cleared.
            return HttpResponseRedirect(redirect_to)
        return super().get(request, *args, **kwargs)


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


class PasswordResetView(PasswordResetView):

    def form_valid(self, form):
        logger.info(f'{form.cleaned_data["email"]} requested a password reset')
        return super().form_valid(form)


class PasswordResetConfirmView(PasswordResetConfirmView):
    post_reset_login = True

    def form_valid(self, form):
        logger.info(f'{self.user} successfully reset their password')
        return super().form_valid(form)