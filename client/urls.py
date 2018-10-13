from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from client import views as client_views


urlpatterns = [
    url(
        r'^login/$',
        client_views.LoginView.as_view(),
        name='login',
    ),
    url(r'^$', client_views.home, name='home'),
    url(r'^sign_out/', auth_views.logout, {'next_page': 'client:login'}, name='sign-out'),

    url(r'^change_password/$', client_views.change_password, name='change-password'),

    url(r'^profile/$', client_views.client_profile, name='profile'),
    url(r'^profile/locations/$', client_views.client_profile_locations, name='profile-locations'),
    url(r'^profile/location/(?P<location_id>\d+)/$', client_views.client_profile_location_detail, name='profile-location-detail'),

    url(r'^inventory/$', client_views.client_inventory, name='inventory'),
    url(r'^inventory/list/$', client_views.client_inventory_list, name='inventory-list'),
    url(r'^inventory/delivery/(?P<shipment_id>\d+)/products/$', client_views.client_delivery_products, name='delivery-products'),
    url(r'^inventory/request_delivery/$', client_views.client_inventory_request_delivery, name='inventory-request_delivery'),

    url(r'^history/$', client_views.client_history, name='history'),

    url(r'^reorder/$', client_views.client_reorder, name='reorder'),

    url(r'^select/(?P<client_id>\d+)/$', client_views.select_client, name='select'),

    url(r'^product/(?P<product_id>\d+)/history/$', client_views.client_product_history, name='product-history'),
    url(r'^shipment/(?P<shipment_id>\d+)/docs/$', client_views.client_shipment_docs, name='shipment-docs'),
]
