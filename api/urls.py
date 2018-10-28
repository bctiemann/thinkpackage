from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from api import views as api_views


urlpatterns = [
    url(r'^clients/$', api_views.GetClients.as_view(), name='clients'),
    url(r'^(?P<client_id>\d+)/products/$', api_views.GetClientProducts.as_view(), name='client-products'),
    url(r'^async_task/(?P<task_id>\d+)/status/$', api_views.AsyncTaskStatus.as_view(), name='async-task-status'),
]
