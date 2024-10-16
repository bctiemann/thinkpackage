from django.urls import path, register_converter
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from client import views as client_views


urlpatterns = [
    path(
        'login/',
        client_views.LoginView.as_view(),
        name='login',
    ),
    path('', client_views.home, name='home'),
    path('sign_out/', ims_views.LogoutView.as_view(next_page='client:login'), name='sign-out'),

    path('change_password/', client_views.change_password, name='change-password'),
    path('dismiss_password_prompt/', client_views.dismiss_password_prompt, name='dismiss-password-prompt'),

    path('profile/', client_views.profile, name='profile'),
    path('profile/locations/', client_views.profile_locations, name='profile-locations'),
    path('profile/location/<int:location_id>/', client_views.profile_location_detail, name='profile-location-detail'),

    path('inventory/', client_views.inventory, name='inventory'),
    path('inventory/list/', client_views.inventory_list, name='inventory-list'),
    path('inventory/delivery/<int:shipment_id>/products/', client_views.delivery_products, name='delivery-products'),
    path('inventory/request_delivery/', client_views.inventory_request_delivery, name='inventory-request_delivery'),

    path('history/', client_views.history, name='history'),

    path('reorder/', client_views.reorder, name='reorder'),

    path('select/<int:client_id>/', client_views.select_client, name='select'),

    path('product/<int:product_id>/history/', client_views.product_history, name='product-history'),
    path('product/<int:product_id>/report/', client_views.product_report, name='product-report'),
    path('shipment/<int:shipment_id>/docs/', client_views.shipment_docs, name='shipment-docs'),
]
