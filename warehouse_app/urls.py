from django.urls import path, register_converter
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from warehouse_app import views as warehouse_app_views
from mgmt import views as mgmt_views


urlpatterns = [
    path(
        'login/',
        warehouse_app_views.LoginView.as_view(),
        name='login',
    ),
    path('', warehouse_app_views.home, name='home'),
    path('menu/', warehouse_app_views.menu, name='menu'),
    path('receive/', warehouse_app_views.receive, name='receive'),
    path('receive/<int:receivable_id>/form/', warehouse_app_views.receive_form, name='receive-form'),
    path('receive/<int:receivable_id>/confirm/', mgmt_views.ReceivableConfirm.as_view(), name='receive-confirm'),
    path('pallet/', warehouse_app_views.pallet, name='pallet'),
    path('pallet/create/', warehouse_app_views.PalletCreate.as_view(), name='pallet-create'),
    path('check_pallet_contents/', warehouse_app_views.check_pallet_contents, name='check-pallet-contents'),
    path('check_product/', warehouse_app_views.check_product, name='check-product'),

    path('barcode/lookup/check_product/', warehouse_app_views.barcode_lookup_product, name='barcode-lookup-product'),
    path('barcode/lookup/check_pallet_contents/', warehouse_app_views.barcode_lookup_pallet_contents, name='barcode-lookup-pallet-contents'),
    path('barcode/lookup/pallet/', warehouse_app_views.barcode_pallet, name='barcode-pallet'),

    path('sign_out/', ims_views.LogoutView.as_view(next_page='warehouse_app:login'), name='sign-out'),
]

