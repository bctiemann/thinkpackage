from django.conf.urls import url, include
from django.contrib import admin

from ims import views as ims_views
from api import views as api_views

urlpatterns_mgmt = [
    url(r'^$', ims_views.mgmt, name='mgmt-home'),

    url(r'^customers_list/$', ims_views.mgmt_customers_list, name='mgmt-customers-list'),
    url(r'^contacts_list/(?P<client_id>\d+)/$', ims_views.mgmt_contacts_list, name='mgmt-contacts-list'),
    url(r'^locations_list/(?P<client_id>\d+)/$', ims_views.mgmt_locations_list, name='mgmt-locations-list'),
    url(r'^location_detail/(?P<location_id>\d+)/$', ims_views.mgmt_locations_list, name='mgmt-locations-list'),

#    url(r'^contact_form/$', ims_views.mgmt_contact_form, name='mgmt-contact-form'),
#    url(r'^location_form/(?P<location_id>\d+)/$', ims_views.mgmt_location_form, name='mgmt-location-form'),

#    url(r'^client/(?P<client_id>\d+)/$', ims_views.ClientUpdate.as_view(), name='mgmt-client-update'),

    url(r'^contact/add/(?P<client_id>\d+)/$', ims_views.CustContactCreate.as_view(), name='mgmt-contact-add'),
    url(r'^contact/(?P<custcontact_id>\d+)/$', ims_views.CustContactUpdate.as_view(), name='mgmt-contact-update'),
    url(r'^contact/(?P<custcontact_id>\d+)/delete/$', ims_views.CustContactDelete.as_view(), name='mgmt-contact-delete'),

    url(r'^location/add/(?P<client_id>\d+)/$', ims_views.LocationCreate.as_view(), name='mgmt-location-add'),
    url(r'^location/(?P<location_id>\d+)/$', ims_views.LocationUpdate.as_view(), name='mgmt-location-update'),
    url(r'^location/(?P<location_id>\d+)/delete/$', ims_views.LocationDelete.as_view(), name='mgmt-location-delete'),

    url(r'^product/add/(?P<client_id>\d+)/$', ims_views.ProductCreate.as_view(), name='mgmt-product-add'),
    url(r'^product/(?P<product_id>\d+)/$', ims_views.ProductUpdate.as_view(), name='mgmt-product-update'),
    url(r'^product/(?P<product_id>\d+)/delete/$', ims_views.ProductDelete.as_view(), name='mgmt-product-delete'),
    url(r'^product/(?P<product_id>\d+)/history/$', ims_views.mgmt_product_history, name='mgmt-product-history'),

    url(r'^receivable/add/(?P<product_id>\d+)/$', ims_views.ReceivableCreate.as_view(), name='mgmt-receivable-create'),
    url(r'^receivable/(?P<receivable_id>\d+)/confirm/$', ims_views.ReceivableConfirm.as_view(), name='mgmt-receivable-confirm'),
    url(r'^receivable/(?P<receivable_id>\d+)/delete/$', ims_views.ReceivableDelete.as_view(), name='mgmt-receivable-delete'),

    url(r'^(?P<client_id>\d+)/$', ims_views.mgmt_redirect, name='mgmt-redirect'),
#    url(r'^(?P<client_id>\d+)/profile/$', ims_views.mgmt_profile, name='mgmt-profile'),
    url(r'^(?P<client_id>\d+)/profile/$', ims_views.ClientUpdate.as_view(), name='mgmt-profile'),
    url(r'^(?P<client_id>\d+)/profile/location=(?P<location_id>\d+)/$', ims_views.mgmt_profile, name='mgmt-profile'),
    url(r'^(?P<client_id>\d+)/profile/contact=(?P<custcontact_id>\d+)/$', ims_views.mgmt_profile, name='mgmt-profile'),
    url(r'^(?P<client_id>\d+)/inventory/(?P<product_id>\d+)?/?$', ims_views.mgmt_inventory, name='mgmt-inventory'),
    url(r'^(?P<client_id>\d+)/shipments/(?P<shipment_id>\d+)?/?$', ims_views.mgmt_shipments, name='mgmt-shipments'),

    url(r'^(?P<client_id>\d+)/inventory/list/$', ims_views.mgmt_inventory_list, name='mgmt-inventory-list'),
    url(r'^(?P<client_id>\d+)/shipments/list/$', ims_views.mgmt_shipments_list, name='mgmt-shipments-list'),

]

urlpatterns_api = [
    url(r'^clients/$', api_views.GetClients.as_view(), name='api-clients'),
    url(r'^(?P<client_id>\d+)/products/$', api_views.GetClientProducts.as_view(), name='api-client-products'),
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$', ims_views.home, name='home'),

    url(r'^mgmt/', include(urlpatterns_mgmt)),
    url(r'^api/', include(urlpatterns_api)),
]
