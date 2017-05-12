from django.conf.urls import url, include
from django.contrib import admin

from ims import views as ims_views

urlpatterns_mgmt = [
    url(r'^$', ims_views.mgmt, name='mgmt-home'),
    url(r'^customers_list/$', ims_views.mgmt_customers_list, name='mgmt-customers-list'),
    url(r'^(?P<client_id>\d+)/$', ims_views.mgmt_redirect, name='mgmt-redirect'),
    url(r'^(?P<client_id>\d+)/profile/$', ims_views.mgmt_profile, name='mgmt-profile'),
    url(r'^(?P<client_id>\d+)/inventory/(?P<product_id>\d+)?/?$', ims_views.mgmt_inventory, name='mgmt-inventory'),
    url(r'^(?P<client_id>\d+)/shipments/(?P<shipment_id>\d+)?/?$', ims_views.mgmt_shipments, name='mgmt-shipments'),
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$', ims_views.home, name='home'),

    url(r'^mgmt/', include(urlpatterns_mgmt)),
]
