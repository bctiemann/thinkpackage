from django.conf.urls import url, include
from django.urls import path, register_converter
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from accounting import views as accounting_views
from mgmt import views as mgmt_views


urlpatterns = [
    path(
        'login/',
        accounting_views.LoginView.as_view(),
        name='login',
    ),
    path('', accounting_views.home, name='home'),
    path('sign_out/', ims_views.LogoutView.as_view(next_page='accounting:login'), name='sign-out'),

    path('shipments/', accounting_views.shipments, name='shipments'),
    path('shipments/list/', accounting_views.shipments_list, name='shipments-list'),
    path('shipments/fetch/', accounting_views.shipments_fetch, name='shipments-fetch'),
    path('shipment/<int:shipment_id>/', accounting_views.ShipmentUpdateInvoice.as_view(), name='shipment-details'),
    path('shipment/<int:shipment_id>/submit/', accounting_views.ShipmentSubmitInvoice.as_view(), name='shipment-submit-invoice'),
    path('shipment/<int:shipment_id>/docs/', ims_views.ShipmentDocCreate.as_view(), name='shipment-docs'),
    path('shipment/doc/<uuid:doc_id>/delete/', ims_views.ShipmentDocDelete.as_view(), name='shipment-doc-delete'),

    path('reconciliation/', accounting_views.reconciliation, name='reconciliation'),
    path('reconciliation/list/', accounting_views.reconciliation_list, name='reconciliation-list'),
    path('reconciliation/<int:returned_product_id>/', accounting_views.ReturnedProductReconcile.as_view(), name='reconciliation-reconcile'),

    path('incoming/', accounting_views.incoming, name='incoming'),
]

