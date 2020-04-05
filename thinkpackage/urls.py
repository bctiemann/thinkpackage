from django.conf import settings
from django.conf.urls import url, include
from django.urls import path, register_converter
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import views as auth_views
from ims import views as ims_views
from ims.converters import CapitalAlphaStringConverter


register_converter(CapitalAlphaStringConverter, 'caps')


urlpatterns = [
    path('admin/', admin.site.urls),

    path('sign_out/', ims_views.LogoutView.as_view(next_page='home'), name='sign-out'),

    path('recovery/password_reset/',
        ims_views.PasswordResetView.as_view(
            template_name='accounts/password_reset_form.html',
            from_email=settings.SUPPORT_EMAIL,
            extra_email_context={
                'site_name': settings.COMPANY_NAME
            },
        ),
        name='password_reset',
    ),
    path('recovery/password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'
    ),
    path('recovery/reset/<uidb64>/<token>/',
         ims_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ),
         name='password_reset_confirm'
    ),
    path('recovery/reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'
    ),

    path('', ims_views.home, name='home'),
    path('shipment/doc/<uuid:doc_id>/', ims_views.shipment_doc, name='shipment-doc'),
    path('pallet/code/<caps:pallet_id>/', ims_views.pallet_code, name='pallet-code'),
    path('product/code/<caps:product_id>/', ims_views.product_code, name='product-code'),

    path(
        'favicon.ico',
        RedirectView.as_view(
            url=staticfiles_storage.url('favicon.ico'),
            permanent=False),
        name='favicon'
    ),

    path('mgmt/', include(('mgmt.urls', 'mgmt'), namespace='mgmt')),
    path('client/', include(('client.urls', 'client'), namespace='client')),
    path('warehouse/', include(('warehouse.urls', 'warehouse'), namespace='warehouse')),
    path('wapp/', include(('warehouse_app.urls', 'warehouse_app'), namespace='warehouse_app')),
    path('accounting/', include(('accounting.urls', 'accounting'), namespace='accounting')),
    path('api/', include(('api.urls', 'api'), namespace='api')),

    path(
        'account/login/',
        ims_views.LoginView.as_view(),
        name='login',
    ),

    path('', include(tf_urls, 'two_factor')),

]
