# -*- coding: utf-8 -*-


from django.shortcuts import render, redirect, get_object_or_404


import logging
logger = logging.getLogger(__name__)
auth_logger = logging.getLogger('auth')


def home(request):
    context = {
    }
    return render(request, 'home.html', context)


def ajax_fragment(request, param):
    context = {'param': param}
    logger.info(f'Fetched ajax fragment with param {param}')
    return render(request, 'ajax_fragment.html', context)

