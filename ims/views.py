# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render


def home(request):
    context = {
    }
    return render(request, 'ims/home.html', context)
