from django.conf.urls import url, include
from django.urls import path, register_converter
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from mgmt import views as mgmt_views
from warehouse import views as warehouse_views


urlpatterns = [
    path(
        'login/',
        warehouse_views.LoginView.as_view(),
        name='login',
    ),

    path('', warehouse_views.home, name='home'),
    path('sign_out/', ims_views.LogoutView.as_view(next_page='warehouse:login'), name='sign-out'),

    path('shipments/', warehouse_views.shipments, name='shipments'),
    path('shipments/list/', warehouse_views.shipments_list, name='shipments-list'),
    path('shipments/fetch/', warehouse_views.shipments_fetch, name='shipments-fetch'),
    path('shipment/<int:shipment_id>/', warehouse_views.ShipmentUpdate.as_view(), name='shipment-details'),
    path('shipment/<int:shipment_id>/mark_ready/', warehouse_views.ShipmentMarkReady.as_view(), name='shipment-mark-ready'),
    path('shipment/<int:shipment_id>/ship/', warehouse_views.ShipmentShip.as_view(), name='shipment-ship'),
    path('shipment/<int:shipment_id>/docs/', ims_views.ShipmentDocCreate.as_view(), name='shipment-docs'),
    path('shipment/doc/<uuid:doc_id>/delete/', ims_views.ShipmentDocDelete.as_view(), name='shipment-doc-delete'),
    path('shipment/<int:shipment_id>/bill_of_lading/', warehouse_views.BillOfLadingView.as_view(), name='bill-of-lading'),
    path('shipment/<int:shipment_id>/purchase_order/', warehouse_views.PurchaseOrderView.as_view(), name='purchase-order'),
    path('shipment/<int:shipment_id>/send_purchase_order/', warehouse_views.SendPurchaseOrder.as_view(), name='send-purchase-order'),

    path('receivables/', warehouse_views.receivables, name='receivables'),
    path('receivables/list/', warehouse_views.receivables_list, name='receivables-list'),
    path('receivables/fetch/', warehouse_views.receivables_fetch, name='receivables-fetch'),

    path('pallets/', warehouse_views.pallets, name='pallets'),
    path('pallet/<int:pallet_id>/', warehouse_views.PalletUpdate.as_view(), name='pallet-details'),
    path('pallet/<int:pallet_id>/delete/', warehouse_views.PalletDelete.as_view(), name='pallet-delete'),
    path('pallet/<int:pallet_id>/print/', ims_views.PalletPrint.as_view(), name='pallet-print'),
]
