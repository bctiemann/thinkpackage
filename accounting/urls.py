from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from accounting import views as accounting_views
from mgmt import views as mgmt_views


urlpatterns = [
    url(
        r'^login/$',
        accounting_views.LoginView.as_view(),
        name='login',
    ),
    url(r'^$', accounting_views.home, name='home'),
    url(r'^sign_out/', ims_views.LogoutView.as_view(next_page='accounting:login'), name='sign-out'),

    url(r'^shipments/$', accounting_views.shipments, name='shipments'),
    url(r'^shipments/list/$', accounting_views.shipments_list, name='shipments-list'),
    url(r'^shipments/fetch/$', accounting_views.shipments_fetch, name='shipments-fetch'),
    url(r'^shipment/(?P<shipment_id>\d+)/$', accounting_views.ShipmentUpdateInvoice.as_view(), name='shipment-details'),
    url(r'^shipment/(?P<shipment_id>\d+)/submit/$', accounting_views.ShipmentSubmitInvoice.as_view(), name='shipment-submit-invoice'),
    url(r'^shipment/(?P<shipment_id>\d+)/docs/$', mgmt_views.ShipmentDocCreate.as_view(), name='shipment-docs'),
    url(r'^shipment/doc/(?P<doc_id>\d+)/delete/$', mgmt_views.ShipmentDocDelete.as_view(), name='shipment-doc-delete'),

    url(r'^reconciliation/$', accounting_views.reconciliation, name='reconciliation'),
    url(r'^reconciliation/list/$', accounting_views.reconciliation_list, name='reconciliation-list'),
    url(r'^reconciliation/(?P<returned_product_id>\d+)/$', accounting_views.ReturnedProductReconcile.as_view(), name='reconciliation-reconcile'),

    url(r'^incoming/$', accounting_views.incoming, name='incoming'),
]

