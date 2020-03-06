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

    url(r'^notifications/delivery_requests/$', mgmt_views.notifications_delivery_requests,
        name='notifications-delivery-requests'),
    url(r'^notifications/ready_to_ship/$', mgmt_views.notifications_ready_to_ship,
        name='notifications-ready-to-ship'),
    url(r'^notifications/inbound_receivables/$', mgmt_views.notifications_inbound_receivables,
        name='notifications-inbound-receivables'),
    url(r'^notifications/invq/$', mgmt_views.notifications_invq,
        name='notifications-invq'),
    url(r'^notifications/low_stock/$', mgmt_views.notifications_low_stock,
        name='notifications-low-stock'),

    url(r'^sign_out/', auth_views.LogoutView.as_view(next_page='mgmt:login'), name='sign-out'),
    # url(r'^password_reset/$', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset_form.html'), name='password-reset'),
    # url(r'^password_reset/done/$', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password-reset-done'),
    # url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password-reset-confirm'),
    # url(r'^reset/done/$', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password-reset-complete'),

    url(r'^customers_list/$', mgmt_views.customers_list, name='customers-list'),
    url(r'^contacts_list/(?P<client_id>\d+)/$', mgmt_views.contacts_list, name='contacts-list'),
    url(r'^locations_list/(?P<client_id>\d+)/$', mgmt_views.locations_list, name='locations-list'),
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
    url(r'^product/(?P<product_id>\d+)/history/$', mgmt_views.product_history, name='product-history'),
    url(r'^product/(?P<product_id>\d+)/transfer/$', mgmt_views.ProductTransfer.as_view(), name='product-transfer'),
    url(r'^product/(?P<product_id>\d+)/return/$', mgmt_views.ProductReturn.as_view(), name='product-return'),

    url(r'^receivable/add/(?P<product_id>\d+)/$', mgmt_views.ReceivableCreate.as_view(), name='receivable-create'),
    url(r'^receivable/(?P<receivable_id>\d+)/confirm/$', mgmt_views.ReceivableConfirm.as_view(), name='receivable-confirm'),
    url(r'^receivable/(?P<receivable_id>\d+)/delete/$', mgmt_views.ReceivableDelete.as_view(), name='receivable-delete'),

    url(r'^shipment/(?P<shipment_id>\d+)/$', mgmt_views.ShipmentDetail.as_view(), name='shipment-detail'),
    url(r'^shipment/(?P<shipment_id>\d+)/delete/$', mgmt_views.ShipmentDelete.as_view(), name='shipment-delete'),
    url(r'^shipment/(?P<shipment_id>\d+)/docs/$', mgmt_views.ShipmentDocCreate.as_view(), name='shipment-docs'),
    url(r'^shipment/doc/(?P<doc_id>\d+)/delete/$', mgmt_views.ShipmentDocDelete.as_view(), name='shipment-doc-delete'),
#    url(r'^shipment/doc/(?P<doc_id>\d+)/$', mgmt_views.mgmt_shipment_doc, name='shipment-doc'),

    url(r'^pallet/(?P<pallet_id>\d+)/print/$', ims_views.PalletPrint.as_view(), name='pallet-print'),
    url(r'^product/(?P<product_id>\d+)/print/$', ims_views.ProductPrint.as_view(), name='product-print'),

    url(r'^report/(?P<async_task_id>[0-9a-f-]+)/$', ims_views.async_task_result, name='async-task-result'),

    url(r'^(?P<client_id>\d+)/$', mgmt_views.redirect, name='redirect'),
#    url(r'^(?P<client_id>\d+)/profile/$', ims_views.mgmt_profile, name='profile'),
    url(r'^client/create/$', mgmt_views.ClientCreate.as_view(), name='client-create'),
    url(r'^(?P<client_id>\d+)/profile/$', mgmt_views.ClientUpdate.as_view(), name='profile'),
    # url(r'^(?P<client_id>\d+)/profile/location=(?P<location_id>\d+)/$', mgmt_views.profile, name='profile'),
    # url(r'^(?P<client_id>\d+)/profile/contact=(?P<custcontact_id>\d+)/$', mgmt_views.profile, name='profile'),
    url(r'^(?P<client_id>\d+)/inventory/(?P<product_id>\d+)?/?$', mgmt_views.inventory, name='inventory'),
    url(r'^(?P<client_id>\d+)/shipments/(?P<shipment_id>\d+)?/?$', mgmt_views.shipments, name='shipments'),

    url(r'^(?P<client_id>\d+)/inventory/list/$', mgmt_views.inventory_list, name='inventory-list'),
    url(r'^(?P<client_id>\d+)/shipments/list/$', mgmt_views.shipments_list, name='shipments-list'),
    url(r'^(?P<client_id>\d+)/shipments/fetch/$', mgmt_views.shipments_fetch, name='shipments-fetch'),

    url(r'^action_log/$', mgmt_views.action_log, name='action-log'),
#    url(r'^action_log/$', mgmt_views.FilteredActionLogListView.as_view(), name='action-log'),
    url(r'^search/$', mgmt_views.search, name='search'),

    url(r'^report/lookup/$', mgmt_views.ItemLookupReport.as_view(), name='item-lookup-report'),
#    url(r'^report/inventory_list/$', mgmt_views.inventory_list_csv, name='inventory-list-report'),
    url(r'^report/inventory_list/$', mgmt_views.InventoryListReport.as_view(), name='inventory-list-report'),
    url(r'^report/delivery_list/$', mgmt_views.DeliveryListReport.as_view(), name='delivery-list-report'),
    url(r'^report/incoming_list/$', mgmt_views.IncomingListReport.as_view(), name='incoming-list-report'),
    url(r'^report/location_list/$', mgmt_views.LocationListReport.as_view(), name='location-list-report'),
    url(r'^report/contact_list/$', mgmt_views.ContactListReport.as_view(), name='contact-list-report'),
]
