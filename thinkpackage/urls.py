from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from mgmt import views as mgmt_views
from client import views as client_views
from api import views as api_views

from ims.forms import UserLoginForm

urlpatterns_mgmt = [
    url(
        r'^account/login/$',
        mgmt_views.LoginView.as_view(),
        name='login',
    ),
     url(
        r'^account/two_factor/backup/phone/register/$',
        mgmt_views.PhoneSetupView.as_view(),
        name='phone_create',
    ),
    url(
        r'^account/two_factor/backup/phone/unregister/(?P<pk>\d+)/$',
        mgmt_views.PhoneDeleteView.as_view(),
        name='phone_delete',
    ),
    url(
        r'^account/two_factor/disable/$',
        mgmt_views.DisableView.as_view(),
        name='disable',
    ),
    url(r'', include('two_factor.urls', 'mgmt-two_factor')),

    url(r'^$', mgmt_views.mgmt, name='mgmt-home'),

#    url(
#        r'^sign_in/',
#        auth_views.login,
#        {
#            'template_name': 'ims/mgmt/sign_in.html',
#            'authentication_form': UserLoginForm,
#        },
#        name='sign-in'
#    ),
    url(r'^sign_out/', auth_views.logout, {'next_page': 'login'}, name='sign-out'),
    url(r'^password_reset/$', auth_views.password_reset, {'template_name': 'accounts/password_reset_form.html',}, name='password-reset'),
    url(r'^password_reset/done/$', auth_views.password_reset_done, {'template_name': 'accounts/password_reset_done.html',},name='password-reset-done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth_views.password_reset_confirm, {'template_name': 'accounts/password_reset_confirm.html',}, name='password-reset-confirm'),
    url(r'^reset/done/$', auth_views.password_reset_complete, {'template_name': 'accounts/password_reset_complete.html',}, name='password-reset-complete'),

    url(r'^customers_list/$', mgmt_views.mgmt_customers_list, name='mgmt-customers-list'),
    url(r'^contacts_list/(?P<client_id>\d+)/$', mgmt_views.mgmt_contacts_list, name='mgmt-contacts-list'),
    url(r'^locations_list/(?P<client_id>\d+)/$', mgmt_views.mgmt_locations_list, name='mgmt-locations-list'),
    url(r'^location_detail/(?P<location_id>\d+)/$', mgmt_views.mgmt_locations_list, name='mgmt-locations-list'),

#    url(r'^contact_form/$', ims_views.mgmt_contact_form, name='mgmt-contact-form'),
#    url(r'^location_form/(?P<location_id>\d+)/$', ims_views.mgmt_location_form, name='mgmt-location-form'),

#    url(r'^client/(?P<client_id>\d+)/$', ims_views.ClientUpdate.as_view(), name='mgmt-client-update'),

    url(r'^contact/add/(?P<client_id>\d+)/$', mgmt_views.CustContactCreate.as_view(), name='mgmt-contact-add'),
    url(r'^contact/(?P<custcontact_id>\d+)/$', mgmt_views.CustContactUpdate.as_view(), name='mgmt-contact-update'),
    url(r'^contact/(?P<custcontact_id>\d+)/delete/$', mgmt_views.CustContactDelete.as_view(), name='mgmt-contact-delete'),

    url(r'^location/add/(?P<client_id>\d+)/$', mgmt_views.LocationCreate.as_view(), name='mgmt-location-add'),
    url(r'^location/(?P<location_id>\d+)/$', mgmt_views.LocationUpdate.as_view(), name='mgmt-location-update'),
    url(r'^location/(?P<location_id>\d+)/delete/$', mgmt_views.LocationDelete.as_view(), name='mgmt-location-delete'),

    url(r'^product/add/(?P<client_id>\d+)/$', mgmt_views.ProductCreate.as_view(), name='mgmt-product-add'),
    url(r'^product/(?P<product_id>\d+)/$', mgmt_views.ProductUpdate.as_view(), name='mgmt-product-update'),
    url(r'^product/(?P<product_id>\d+)/delete/$', mgmt_views.ProductDelete.as_view(), name='mgmt-product-delete'),
    url(r'^product/(?P<product_id>\d+)/history/$', mgmt_views.mgmt_product_history, name='mgmt-product-history'),
    url(r'^product/(?P<product_id>\d+)/transfer/$', mgmt_views.ProductTransfer.as_view(), name='mgmt-product-transfer'),

    url(r'^receivable/add/(?P<product_id>\d+)/$', mgmt_views.ReceivableCreate.as_view(), name='mgmt-receivable-create'),
    url(r'^receivable/(?P<receivable_id>\d+)/confirm/$', mgmt_views.ReceivableConfirm.as_view(), name='mgmt-receivable-confirm'),
    url(r'^receivable/(?P<receivable_id>\d+)/delete/$', mgmt_views.ReceivableDelete.as_view(), name='mgmt-receivable-delete'),

    url(r'^shipment/(?P<shipment_id>\d+)/$', mgmt_views.ShipmentDetail.as_view(), name='mgmt-shipment-detail'),
    url(r'^shipment/(?P<shipment_id>\d+)/docs/$', mgmt_views.ShipmentDocCreate.as_view(), name='mgmt-shipment-docs'),
    url(r'^shipment/doc/(?P<doc_id>\d+)/delete/$', mgmt_views.ShipmentDocDelete.as_view(), name='mgmt-shipment-doc-delete'),
#    url(r'^shipment/doc/(?P<doc_id>\d+)/$', mgmt_views.mgmt_shipment_doc, name='mgmt-shipment-doc'),

    url(r'^(?P<client_id>\d+)/$', mgmt_views.mgmt_redirect, name='mgmt-redirect'),
#    url(r'^(?P<client_id>\d+)/profile/$', ims_views.mgmt_profile, name='mgmt-profile'),
    url(r'^(?P<client_id>\d+)/profile/$', mgmt_views.ClientUpdate.as_view(), name='mgmt-profile'),
    url(r'^(?P<client_id>\d+)/profile/location=(?P<location_id>\d+)/$', mgmt_views.mgmt_profile, name='mgmt-profile'),
    url(r'^(?P<client_id>\d+)/profile/contact=(?P<custcontact_id>\d+)/$', mgmt_views.mgmt_profile, name='mgmt-profile'),
    url(r'^(?P<client_id>\d+)/inventory/(?P<product_id>\d+)?/?$', mgmt_views.mgmt_inventory, name='mgmt-inventory'),
    url(r'^(?P<client_id>\d+)/shipments/(?P<shipment_id>\d+)?/?$', mgmt_views.mgmt_shipments, name='mgmt-shipments'),

    url(r'^(?P<client_id>\d+)/inventory/list/$', mgmt_views.mgmt_inventory_list, name='mgmt-inventory-list'),
    url(r'^(?P<client_id>\d+)/shipments/list/$', mgmt_views.mgmt_shipments_list, name='mgmt-shipments-list'),
]

urlpatterns_client = [
    url(
        r'^account/login/$',
        client_views.LoginView.as_view(),
        name='login',
    ),
     url(
        r'^account/two_factor/backup/phone/register/$',
        client_views.PhoneSetupView.as_view(),
        name='phone_create',
    ),
    url(
        r'^account/two_factor/backup/phone/unregister/(?P<pk>\d+)/$',
        client_views.PhoneDeleteView.as_view(),
        name='phone_delete',
    ),
    url(
        r'^account/two_factor/disable/$',
        client_views.DisableView.as_view(),
        name='disable',
    ),
    url(r'', include('two_factor.urls', 'client-two_factor')),
#    url(
#        r'^sign_in/',
#        auth_views.login,
#        {
#            'template_name': 'client/sign_in.html',
#            'authentication_form': UserLoginForm,
#        },
#        name='sign-in'
#    ),

    url(r'^$', client_views.client, name='client-home'),

    url(r'^profile/$', client_views.client_profile, name='client-profile'),
    url(r'^inventory/$', client_views.client_inventory, name='client-inventory'),
    url(r'^inventory/list/$', client_views.client_inventory_list, name='client-inventory-list'),
    url(r'^history/$', client_views.client_history, name='client-history'),
    url(r'^reorder/$', client_views.client_reorder, name='client-reorder'),

    url(r'^select/(?P<client_id>\d+)/$', client_views.select_client, name='client-select'),

    url(r'^product/(?P<product_id>\d+)/history/$', client_views.client_product_history, name='client-product-history'),
    url(r'^shipment/(?P<shipment_id>\d+)/docs/$', client_views.client_shipment_docs, name='client-shipment-docs'),
]

urlpatterns_api = [
    url(r'^clients/$', api_views.GetClients.as_view(), name='api-clients'),
    url(r'^(?P<client_id>\d+)/products/$', api_views.GetClientProducts.as_view(), name='api-client-products'),
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$', ims_views.home, name='home'),
    url(r'^shipment/doc/(?P<doc_id>\d+)/$', ims_views.shipment_doc, name='shipment-doc'),

    url(
        r'^favicon.ico$',
        RedirectView.as_view(
            url=staticfiles_storage.url('favicon.ico'),
            permanent=False),
        name="favicon"
    ),

    url(r'^mgmt/', include(urlpatterns_mgmt)),
    url(r'^client/', include(urlpatterns_client)),
    url(r'^api/', include(urlpatterns_api)),
]
