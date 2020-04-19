from django.conf.urls import url, include
from django.urls import path, re_path, register_converter
from django.contrib.auth import views as auth_views

from ims import views as ims_views
from mgmt import views as mgmt_views


urlpatterns = [
    path(
        'login/',
        mgmt_views.LoginView.as_view(),
        name='login',
    ),

    path('', mgmt_views.home, name='home'),

    path('notifications/delivery_requests/', mgmt_views.notifications_delivery_requests,
        name='notifications-delivery-requests'),
    path('notifications/ready_to_ship/', mgmt_views.notifications_ready_to_ship,
        name='notifications-ready-to-ship'),
    path('notifications/inbound_receivables/', mgmt_views.notifications_inbound_receivables,
        name='notifications-inbound-receivables'),
    path('notifications/invq/', mgmt_views.notifications_invq,
        name='notifications-invq'),
    path('notifications/low_stock/', mgmt_views.notifications_low_stock,
        name='notifications-low-stock'),

    path('sign_out/', ims_views.LogoutView.as_view(next_page='mgmt:login'), name='sign-out'),

    # path('customers_list/', mgmt_views.customers_list, name='customers-list'),
    # path('contacts_list/<int:client_id>/', mgmt_views.contacts_list, name='contacts-list'),
    # path('locations_list/<int:client_id>/', mgmt_views.locations_list, name='locations-list'),
    #
    # path('contact/add/<int:client_id>/', mgmt_views.CustContactCreate.as_view(), name='contact-add'),
    # path('contact/<int:custcontact_id>/', mgmt_views.CustContactUpdate.as_view(), name='contact-update'),
    # path('contact/<int:custcontact_id>/delete/', mgmt_views.CustContactDelete.as_view(), name='contact-delete'),
    #
    # path('location/add/<int:client_id>/', mgmt_views.LocationCreate.as_view(), name='location-add'),
    # path('location/<int:location_id>/', mgmt_views.LocationUpdate.as_view(), name='location-update'),
    # path('location/<int:location_id>/delete/', mgmt_views.LocationDelete.as_view(), name='location-delete'),
    #
    # path('product/add/<int:client_id>/', mgmt_views.ProductCreate.as_view(), name='product-add'),
    # path('product/<int:product_id>/', mgmt_views.ProductUpdate.as_view(), name='product-update'),
    # path('product/<int:product_id>/delete/', mgmt_views.ProductDelete.as_view(), name='product-delete'),
    # path('product/<int:product_id>/history/', mgmt_views.product_history, name='product-history'),
    # path('product/<int:product_id>/transfer/', mgmt_views.ProductTransfer.as_view(), name='product-transfer'),
    # path('product/<int:product_id>/return/', mgmt_views.ProductReturn.as_view(), name='product-return'),
    #
    # path('receivable/add/<int:product_id>/', mgmt_views.ReceivableCreate.as_view(), name='receivable-create'),
    # path('receivable/<int:receivable_id>/confirm/', mgmt_views.ReceivableConfirm.as_view(), name='receivable-confirm'),
    # path('receivable/<int:receivable_id>/delete/', mgmt_views.ReceivableDelete.as_view(), name='receivable-delete'),
    #
    # path('shipment/<int:shipment_id>/', mgmt_views.ShipmentDetail.as_view(), name='shipment-detail'),
    # path('shipment/<int:shipment_id>/delete/', mgmt_views.ShipmentDelete.as_view(), name='shipment-delete'),
    # path('shipment/<int:shipment_id>/docs/', ims_views.ShipmentDocCreate.as_view(), name='shipment-docs'),
    # path('shipment/doc/<uuid:doc_id>/delete/', ims_views.ShipmentDocDelete.as_view(), name='shipment-doc-delete'),
    #
    # path('pallet/<int:pallet_id>/print/', ims_views.PalletPrint.as_view(), name='pallet-print'),
    # path('product/<int:product_id>/print/', ims_views.ProductPrint.as_view(), name='product-print'),
    #
    # path('report/<uuid:async_task_id>/', ims_views.async_task_result, name='async-task-result'),
    #
    # path('<int:client_id>/', mgmt_views.redirect, name='redirect'),
    # path('client/create/', mgmt_views.ClientCreate.as_view(), name='client-create'),
    # path('<int:client_id>/profile/', mgmt_views.ClientUpdate.as_view(), name='profile'),
    # path('<int:client_id>/inventory/', mgmt_views.inventory, name='inventory'),
    # path('<int:client_id>/inventory/<int:product_id>/<product_view>/', mgmt_views.inventory, name='inventory'),
    # path('<int:client_id>/shipments/', mgmt_views.shipments, name='shipments'),
    # path('<int:client_id>/shipments/<int:shipment_id>/', mgmt_views.shipments, name='shipments'),
    #
    # path('<int:client_id>/inventory/list/', mgmt_views.inventory_list, name='inventory-list'),
    # path('<int:client_id>/shipments/list/', mgmt_views.shipments_list, name='shipments-list'),
    # path('<int:client_id>/shipments/fetch/', mgmt_views.shipments_fetch, name='shipments-fetch'),
    #
    # path('action_log/', mgmt_views.action_log, name='action-log'),
    # # path('action_log/', mgmt_views.FilteredActionLogListView.as_view(), name='action-log'),
    # path('search/', mgmt_views.search, name='search'),
    #
    # path('report/lookup/', mgmt_views.ItemLookupReport.as_view(), name='item-lookup-report'),
    # path('report/inventory_list/', mgmt_views.InventoryListReport.as_view(), name='inventory-list-report'),
    # path('report/delivery_list/', mgmt_views.DeliveryListReport.as_view(), name='delivery-list-report'),
    # path('report/incoming_list/', mgmt_views.IncomingListReport.as_view(), name='incoming-list-report'),
    # path('report/product_list/', mgmt_views.ProductListReport.as_view(), name='product-list-report'),
    # path('report/location_list/', mgmt_views.LocationListReport.as_view(), name='location-list-report'),
    # path('report/contact_list/', mgmt_views.ContactListReport.as_view(), name='contact-list-report'),
]
