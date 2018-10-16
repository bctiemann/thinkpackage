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
    url(r'^sign_out/', auth_views.logout, {'next_page': 'warehouse_app:login'}, name='sign-out'),
]

