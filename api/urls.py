from django.conf.urls import url, include
from django.urls import path, register_converter
from django.contrib import admin
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from api import views as api_views


urlpatterns = [
    path('clients/', api_views.GetClients.as_view(), name='clients'),
    path('<int:client_id>/products/', api_views.GetClientProducts.as_view(), name='client-products'),
    path('async_task/<uuid:task_id>/status/', api_views.AsyncTaskStatus.as_view(), name='async-task-status'),

    path('users-ac/<term>/', api_views.AutocompleteUsers.as_view(), name='autocomplete-users'),
    path('user/<int:user_id>/', api_views.UserAPIView.as_view(), name='user'),
]
