from django.conf.urls import url
from django.contrib import admin

from ims import views as ims_views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$', ims_views.home, name='home'),
]
