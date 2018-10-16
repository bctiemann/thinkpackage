# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from django.db.models import Sum, Q
from django.contrib.auth import authenticate, login

from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from ims.models import Product, Transaction, Shipment, ShipmentDoc, Client, ClientUser, Location, ReturnedProduct
from ims.forms import AjaxableResponseMixin, UserLoginForm
from accounting import forms
from ims import utils

from datetime import datetime, timedelta
import json
import re

import logging
logger = logging.getLogger(__name__)


class LoginView(LoginView):
    template_name = 'warehouse_app/login.html'
    form_list = (
        ('auth', UserLoginForm),
        ('token', AuthenticationTokenForm),
        ('backup', BackupTokenForm),
    )


def home(request):

    context = {
    }
    return render(request, 'warehouse_app/home.html', context)


def menu(request):

    context = {
    }
    return render(request, 'warehouse_app/menu.html', context)


def receive(request):

    context = {
    }
    return render(request, 'warehouse_app/receive.html', context)


def pallet(request):

    context = {
    }
    return render(request, 'warehouse_app/pallet.html', context)


def check_pallet_contents(request):

    context = {
    }
    return render(request, 'warehouse_app/check_pallet_contents.html', context)


def check_product(request):

    context = {
    }
    return render(request, 'warehouse_app/check_product.html', context)

