# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render


def client_inventory(request):

    context = {
    }
    return render(request, 'client/inventory.html', context)

