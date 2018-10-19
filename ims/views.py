# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Func, F, Count
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden, HttpResponseRedirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied

from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ims.models import User, Client, Shipment, Transaction, Product, CustContact, Location, Receivable, ShipmentDoc, ClientUser, Pallet
from ims.forms import AjaxableResponseMixin, UserLoginForm
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

    filename = os.path.join(settings.MEDIA_ROOT, shipment_doc.file.name)
    if not os.path.isfile(filename):
        raise Http404

    with open(filename, 'r') as file:
        response = HttpResponse(file.read(), content_type=shipment_doc.content_type)
        response['Content-Disposition'] = 'inline;filename=\'{0}.{1}\''.format(shipment_doc.basename, shipment_doc.ext)
    return response


def pallet_code(request, pallet_id=None):
    pallet = get_object_or_404(Pallet, pallet_id=pallet_id)

#    if not (request.user.is_authenticated):
#        raise PermissionDenied

    response = HttpResponse(content_type='image/png')
    base_image = pallet.get_qrcode(format='PNG')
    base_image.save(response, 'PNG')
    return response


class LoginView(LoginView):
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

