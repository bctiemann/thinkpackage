from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from warehouse_app import views as warehouse_app_views


urlpatterns = [
    url(
        r'^login/$',
        warehouse_app_views.LoginView.as_view(),
        name='login',
    ),
    url(r'^$', warehouse_app_views.home, name='home'),
    url(r'^menu/$', warehouse_app_views.menu, name='menu'),
    url(r'^receive/$', warehouse_app_views.receive, name='receive'),
    url(r'^pallet/$', warehouse_app_views.pallet, name='pallet'),
    url(r'^check_pallet_contents/$', warehouse_app_views.check_pallet_contents, name='check-pallet-contents'),
    url(r'^check_product/$', warehouse_app_views.check_product, name='check-product'),

    url(r'^sign_out/', auth_views.logout, {'next_page': 'warehouse_app:login'}, name='sign-out'),
]

