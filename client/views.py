# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from ims.forms import UserLoginForm


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
        'products': selected_client.product_set.filter(is_deleted=False, is_active=True),
    }
    return render(request, 'client/history.html', context)


def client_reorder(request):

    context = {
    }
    return render(request, 'client/reorder.html', context)

