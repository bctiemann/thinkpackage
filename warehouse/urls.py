from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from warehouse import views as warehouse_views


urlpatterns = [
    url(
        r'^login/$',
        warehouse_views.LoginView.as_view(),
        name='login',
    ),

    url(r'^$', warehouse_views.home, name='home'),
    url(r'^sign_out/', auth_views.LogoutView.as_view(next_page='warehouse:login'), name='sign-out'),

    url(r'^shipments/$', warehouse_views.shipments, name='shipments'),
    url(r'^shipments/list/$', warehouse_views.shipments_list, name='shipments-list'),
    url(r'^shipment/(?P<shipment_id>\d+)/$', warehouse_views.ShipmentUpdate.as_view(), name='shipment-details'),
    url(r'^shipment/(?P<shipment_id>\d+)/ship/$', warehouse_views.ShipmentShip.as_view(), name='shipment-ship'),
    url(r'^shipment/(?P<shipment_id>\d+)/docs/$', warehouse_views.ShipmentDocCreate.as_view(), name='shipment-docs'),
    url(r'^shipment/(?P<shipment_id>\d+)/bill_of_lading/$', warehouse_views.BillOfLadingView.as_view(), name='bill-of-lading'),
    url(r'^shipment/(?P<shipment_id>\d+)/purchase_order/$', warehouse_views.PurchaseOrderView.as_view(), name='purchase-order'),
    url(r'^shipment/doc/(?P<doc_id>\d+)/delete/$', warehouse_views.ShipmentDocDelete.as_view(), name='shipment-doc-delete'),

    url(r'^shipment/(?P<shipment_id>\d+)/purchase_order_test/$', warehouse_views.purchase_order_test, name='purchase-order-test'),

    url(r'^receivables/$', warehouse_views.receivables, name='receivables'),
    url(r'^receivables/list/$', warehouse_views.receivables_list, name='receivables-list'),

    url(r'^pallets/$', warehouse_views.pallets, name='pallets'),
    url(r'^pallet/(?P<pallet_id>\d+)/$', warehouse_views.PalletUpdate.as_view(), name='pallet-details'),
    url(r'^pallet/(?P<pallet_id>\d+)/delete/$', warehouse_views.PalletDelete.as_view(), name='pallet-delete'),
    url(r'^pallet/(?P<pallet_id>\d+)/print/$', ims_views.PalletPrint.as_view(), name='pallet-print'),
]
