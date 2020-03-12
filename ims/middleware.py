from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
from django.urls import resolve, reverse, reverse_lazy
from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin

from ims.models import Client, ClientUser

import logging
logger = logging.getLogger(__name__)


class LoginRequiredMiddleware(MiddlewareMixin):
    """
    Middleware that requires a user to be authenticated to view any page other
    than LOGIN_URL. Exemptions to this requirement can optionally be specified
    in settings by setting a tuple of routes to ignore
    """
    def process_request(self, request):
        assert hasattr(request, 'user'), """
        The Login Required middleware needs to be after AuthenticationMiddleware.
        Also make sure to include the template context_processor:
        'django.contrib.auth.context_processors.auth'."""

        if not request.user.is_authenticated:
            resolved = resolve(request.path_info)
            current_route_name = resolved.url_name

            if not current_route_name in settings.AUTH_EXEMPT_ROUTES:
                if resolved.app_name == 'mgmt':
                    return HttpResponseRedirect(reverse(settings.MGMT_AUTH_LOGIN_ROUTE))
                elif resolved.app_name == 'client':
                    return HttpResponseRedirect(reverse(settings.CLIENT_AUTH_LOGIN_ROUTE))
                elif resolved.app_name == 'accounting':
                    return HttpResponseRedirect(reverse(settings.ACCOUNTING_AUTH_LOGIN_ROUTE))
                elif resolved.app_name == 'warehouse':
                    return HttpResponseRedirect(reverse(settings.WAREHOUSE_AUTH_LOGIN_ROUTE))
                elif resolved.app_name == 'warehouse_app':
                    return HttpResponseRedirect(reverse(settings.WAREHOUSE_APP_AUTH_LOGIN_ROUTE))


class SelectedClientMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def get_selected_client(self, request):
        "Get the selected client from the session store, and set it to the first matching one if not already set or invalid"
        if not request.user.is_authenticated:
            return None
        try:
            if 'selected_client_id' in request.session:
                try:
                    client = Client.objects.get(pk=request.session['selected_client_id'], is_active=True)
                    if request.user.is_admin:
                        return client
                    if ClientUser.objects.filter(user=request.user, client__id__in=client.ancestors).count() == 0:
                        client = None
                except ClientUser.DoesNotExist:
                    client = ClientUser.objects.filter(user=request.user, client__is_active=True).first().client
                    if client:
                        request.session['selected_client_id'] = client.id
                return client
            else:
                try:
                    client = ClientUser.objects.filter(user=request.user, client__is_active=True).first().client
                except AttributeError:
                    logger.debug('No client for user {0}'.format(request.user))
                    return None
                if client:
                    request.session['selected_client_id'] = client.id
            return client
        except Exception as e:
            logger.info(e)
            return None

    def __call__(self, request):
        request.selected_client = self.get_selected_client(request)
        return self.get_response(request)


class PermissionsMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def is_authorized_for_client(self, user, client):
        if not client:
            return False
        if user.is_admin:
            return True
        return ClientUser.objects.filter(user=user, client__id__in=client.ancestors).exists()

    def __call__(self, request):
        resolved = resolve(request.path_info)
        if request.user.is_authenticated:
            if resolved.app_name == 'mgmt' and not request.user.is_admin:
                logger.info(f'{request.user} not authorized for mgmt.')
                raise PermissionDenied
            if resolved.app_name == 'client' and not self.is_authorized_for_client(request.user, request.selected_client):
                logger.info(f'Unauthorized client login ({request.user} for {request.selected_client}).')
                raise PermissionDenied(f'No clients assigned to user {request.user}.')
            if resolved.app_name == 'warehouse' and not request.user.is_warehouse:
                logger.info(f'{request.user} not authorized for warehouse.')
                raise PermissionDenied
            if resolved.app_name == 'warehouse_app' and not request.user.is_warehouse:
                logger.info(f'{request.user} not authorized for warehouse app.')
                raise PermissionDenied
            if resolved.app_name == 'accounting' and not request.user.is_accounting:
                logger.info(f'{request.user} not authorized for accounting.')
                raise PermissionDenied

        return self.get_response(request)
