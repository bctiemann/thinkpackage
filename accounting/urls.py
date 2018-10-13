from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from accounting import views as accounting_views


urlpatterns = [
    url(
        r'^account/login/$',
        accounting_views.LoginView.as_view(),
        name='login',
    ),
    url(r'^$', accounting_views.home, name='home'),
    url(r'^sign_out/', auth_views.logout, {'next_page': 'accounting:login'}, name='sign-out'),

    url(r'^shipments/$', accounting_views.accounting_shipments, name='shipments'),
    url(r'^shipments/list/$', accounting_views.accounting_shipments_list, name='shipments-list'),

    url(r'^reconciliation/$', accounting_views.accounting_reconciliation, name='reconciliation'),
    url(r'^reconciliation/list/$', accounting_views.accounting_reconciliation_list, name='reconciliation-list'),

    url(r'^incoming/$', accounting_views.accounting_incoming, name='incoming'),
]

