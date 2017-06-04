# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from ims.models import Product, Transaction, Shipment
from ims.forms import UserLoginForm

from datetime import datetime, timedelta


class LoginView(LoginView):
    template_name = 'client/login.html'
    form_list = (
        ('auth', UserLoginForm),
        ('token', AuthenticationTokenForm),
        ('backup', BackupTokenForm),
    )


class PhoneSetupView(PhoneSetupView):
    success_url = reverse_lazy('two_factor:profile')


class PhoneDeleteView(PhoneDeleteView):
    success_url = reverse_lazy('two_factor:profile')


class DisableView(DisableView):
    success_url = reverse_lazy('two_factor:profile')


def client(request):
    return redirect('client-inventory')


def client_profile(request):

    context = {
    }
    return render(request, 'client/profile.html', context)


def client_inventory(request):

    context = {
        'selected_client': request.user.get_selected_client(request),
    }
    return render(request, 'client/inventory.html', context)


def client_history(request):

    selected_client = request.user.get_selected_client(request)

    context = {
        'selected_client': selected_client,
        'products': selected_client.product_set.filter(is_deleted=False, is_active=True).order_by('item_number'),
    }
    return render(request, 'client/history.html', context)


def client_reorder(request):

    context = {
    }
    return render(request, 'client/reorder.html', context)


def client_product_history(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    date_to = timezone.now()
    date_from = date_to - timedelta(days=90)
    try:
        date_from = datetime.strptime(request.GET.get('fromdate', ''), '%m/%d/%Y')
        date_to = datetime.strptime(request.GET.get('todate', ''), '%m/%d/%Y')
    except:
        pass

    history = Transaction.objects.filter(product=product, date_created__gt=date_from, date_created__lte=date_to).order_by('-date_created')

#    request.session['selected_client'] = 241

    context = {
        'product': product,
        'history': history,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'client/product_history.html', context)


def client_shipment_docs(request, shipment_id):
    shipment = get_object_or_404(Shipment, pk=shipment_id)

    context = {
        'shipment': shipment,
    }
    return render(request, 'client/shipment_docs.html', context)
