# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
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



def client_inventory(request):

    context = {
    }
    return render(request, 'client/inventory.html', context)

