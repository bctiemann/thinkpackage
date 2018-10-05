from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^sign_out/', auth_views.logout, {'next_page': 'home'}, name='sign-out'),

    url(r'^recovery/password_reset/$', auth_views.password_reset, {'template_name': 'accounts/password_reset_form.html',}, name='password_reset'),
    url(r'^recovery/password_reset/done/$', auth_views.password_reset_done, {'template_name': 'accounts/password_reset_done.html',},name='password_reset_done'),
    url(r'^recovery/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth_views.password_reset_confirm, {'template_name': 'accounts/password_reset_confirm.html',}, name='password_reset_confirm'),
    url(r'^recovery/reset/done/$', auth_views.password_reset_complete, {'template_name': 'accounts/password_reset_complete.html',}, name='password_reset_complete'),

    url(r'^$', ims_views.home, name='home'),
    url(r'^shipment/doc/(?P<doc_id>\d+)/$', ims_views.shipment_doc, name='shipment-doc'),
    url(r'^pallet/code/(?P<pallet_id>[A-Z]+)/$', ims_views.pallet_code, name='pallet-code'),

    url(
        r'^favicon.ico$',
        RedirectView.as_view(
            url=staticfiles_storage.url('favicon.ico'),
            permanent=False),
        name="favicon"
    ),

    url(r'^mgmt/', include('mgmt.urls', 'mgmt')),
    url(r'^client/', include('client.urls', 'client')),
    url(r'^warehouse/', include('warehouse.urls', 'warehouse')),
    url(r'^api/', include('api.urls', 'api')),

    url(r'', include(tf_urls, 'two_factor')),

]
