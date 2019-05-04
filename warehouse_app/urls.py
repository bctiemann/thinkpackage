from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from warehouse_app import views as warehouse_app_views
from mgmt import views as mgmt_views


urlpatterns = [
    url(
        r'^login/$',
        warehouse_app_views.LoginView.as_view(),
        name='login',
    ),
    url(r'^$', warehouse_app_views.home, name='home'),
    url(r'^menu/$', warehouse_app_views.menu, name='menu'),
    url(r'^receive/$', warehouse_app_views.receive, name='receive'),
    url(r'^receive/(?P<receivable_id>\d+)/form/$', warehouse_app_views.receive_form, name='receive-form'),
    url(r'^receive/(?P<receivable_id>\d+)/confirm/$', mgmt_views.ReceivableConfirm.as_view(), name='receive-confirm'),
    url(r'^pallet/$', warehouse_app_views.pallet, name='pallet'),
    url(r'^pallet/create/$', warehouse_app_views.PalletCreate.as_view(), name='pallet-create'),
    url(r'^check_pallet_contents/$', warehouse_app_views.check_pallet_contents, name='check-pallet-contents'),
    url(r'^check_product/$', warehouse_app_views.check_product, name='check-product'),

    url(r'^barcode/lookup/check_product/$', warehouse_app_views.barcode_lookup_product, name='barcode-lookup-product'),
    url(r'^barcode/lookup/check_pallet_contents/$', warehouse_app_views.barcode_lookup_pallet_contents, name='barcode-lookup-pallet-contents'),
    url(r'^barcode/lookup/pallet/$', warehouse_app_views.barcode_pallet, name='barcode-pallet'),

    url(r'^sign_out/', auth_views.LogoutView.as_view(next_page='warehouse_app:login'), name='sign-out'),
]

