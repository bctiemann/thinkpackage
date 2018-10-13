from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from mgmt import views as mgmt_views


urlpatterns = [
    url(
        r'^login/$',
        mgmt_views.LoginView.as_view(),
        name='login',
    ),

    url(r'^$', mgmt_views.home, name='home'),

    url(r'^sign_out/', auth_views.logout, {'next_page': 'mgmt:login'}, name='sign-out'),
    url(r'^password_reset/$', auth_views.password_reset, {'template_name': 'accounts/password_reset_form.html',}, name='password-reset'),
    url(r'^password_reset/done/$', auth_views.password_reset_done, {'template_name': 'accounts/password_reset_done.html',},name='password-reset-done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth_views.password_reset_confirm, {'template_name': 'accounts/password_reset_confirm.html',}, name='password-reset-confirm'),
    url(r'^reset/done/$', auth_views.password_reset_complete, {'template_name': 'accounts/password_reset_complete.html',}, name='password-reset-complete'),

    url(r'^customers_list/$', mgmt_views.mgmt_customers_list, name='customers-list'),
    url(r'^contacts_list/(?P<client_id>\d+)/$', mgmt_views.mgmt_contacts_list, name='contacts-list'),
    url(r'^locations_list/(?P<client_id>\d+)/$', mgmt_views.mgmt_locations_list, name='locations-list'),
#    url(r'^location_detail/(?P<location_id>\d+)/$', mgmt_views.mgmt_locations_list, name='locations-list'),

#    url(r'^contact_form/$', ims_views.mgmt_contact_form, name='contact-form'),
#    url(r'^location_form/(?P<location_id>\d+)/$', ims_views.mgmt_location_form, name='location-form'),

#    url(r'^client/(?P<client_id>\d+)/$', ims_views.ClientUpdate.as_view(), name='client-update'),

    url(r'^contact/add/(?P<client_id>\d+)/$', mgmt_views.CustContactCreate.as_view(), name='contact-add'),
    url(r'^contact/(?P<custcontact_id>\d+)/$', mgmt_views.CustContactUpdate.as_view(), name='contact-update'),
    url(r'^contact/(?P<custcontact_id>\d+)/delete/$', mgmt_views.CustContactDelete.as_view(), name='contact-delete'),

    url(r'^location/add/(?P<client_id>\d+)/$', mgmt_views.LocationCreate.as_view(), name='location-add'),
    url(r'^location/(?P<location_id>\d+)/$', mgmt_views.LocationUpdate.as_view(), name='location-update'),
    url(r'^location/(?P<location_id>\d+)/delete/$', mgmt_views.LocationDelete.as_view(), name='location-delete'),

    url(r'^product/add/(?P<client_id>\d+)/$', mgmt_views.ProductCreate.as_view(), name='product-add'),
    url(r'^product/(?P<product_id>\d+)/$', mgmt_views.ProductUpdate.as_view(), name='product-update'),
    url(r'^product/(?P<product_id>\d+)/delete/$', mgmt_views.ProductDelete.as_view(), name='product-delete'),
    url(r'^product/(?P<product_id>\d+)/history/$', mgmt_views.mgmt_product_history, name='product-history'),
    url(r'^product/(?P<product_id>\d+)/transfer/$', mgmt_views.ProductTransfer.as_view(), name='product-transfer'),
    url(r'^product/(?P<product_id>\d+)/return/$', mgmt_views.ProductReturn.as_view(), name='product-return'),

    url(r'^receivable/add/(?P<product_id>\d+)/$', mgmt_views.ReceivableCreate.as_view(), name='receivable-create'),
    url(r'^receivable/(?P<receivable_id>\d+)/confirm/$', mgmt_views.ReceivableConfirm.as_view(), name='receivable-confirm'),
    url(r'^receivable/(?P<receivable_id>\d+)/delete/$', mgmt_views.ReceivableDelete.as_view(), name='receivable-delete'),

    url(r'^shipment/(?P<shipment_id>\d+)/$', mgmt_views.ShipmentDetail.as_view(), name='shipment-detail'),
    url(r'^shipment/(?P<shipment_id>\d+)/docs/$', mgmt_views.ShipmentDocCreate.as_view(), name='shipment-docs'),
    url(r'^shipment/doc/(?P<doc_id>\d+)/delete/$', mgmt_views.ShipmentDocDelete.as_view(), name='shipment-doc-delete'),
#    url(r'^shipment/doc/(?P<doc_id>\d+)/$', mgmt_views.mgmt_shipment_doc, name='shipment-doc'),

    url(r'^(?P<client_id>\d+)/$', mgmt_views.mgmt_redirect, name='redirect'),
#    url(r'^(?P<client_id>\d+)/profile/$', ims_views.mgmt_profile, name='profile'),
    url(r'^(?P<client_id>\d+)/profile/$', mgmt_views.ClientUpdate.as_view(), name='profile'),
    url(r'^(?P<client_id>\d+)/profile/location=(?P<location_id>\d+)/$', mgmt_views.mgmt_profile, name='profile'),
    url(r'^(?P<client_id>\d+)/profile/contact=(?P<custcontact_id>\d+)/$', mgmt_views.mgmt_profile, name='profile'),
    url(r'^(?P<client_id>\d+)/inventory/(?P<product_id>\d+)?/?$', mgmt_views.mgmt_inventory, name='inventory'),
    url(r'^(?P<client_id>\d+)/shipments/(?P<shipment_id>\d+)?/?$', mgmt_views.mgmt_shipments, name='shipments'),

    url(r'^(?P<client_id>\d+)/inventory/list/$', mgmt_views.mgmt_inventory_list, name='inventory-list'),
    url(r'^(?P<client_id>\d+)/shipments/list/$', mgmt_views.mgmt_shipments_list, name='shipments-list'),

    url(r'^action_log/$', mgmt_views.mgmt_action_log, name='action-log'),
#    url(r'^action_log/$', mgmt_views.FilteredActionLogListView.as_view(), name='action-log'),
]
