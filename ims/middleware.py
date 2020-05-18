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
            logger.info(f'{current_route_name} {resolved.app_name}')

            if not resolved.app_name or resolved.app_name == 'admin':
                return None

            if current_route_name not in settings.AUTH_EXEMPT_ROUTES:
                if resolved.app_name == 'api':
                    logger.info('redirecting to login from api')
                    return HttpResponseRedirect(reverse('login'))
                if resolved.app_name:
                    logger.info(f'redirecting to login from {resolved.app_name}')
                    return HttpResponseRedirect(reverse(f'{resolved.app_name}:login'))
                logger.info('redirecting to login with no app_name')
                return HttpResponseRedirect(reverse('login'))


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
                    # Admins have access to all valid clients
                    if request.user.is_admin:
                        return client
                    # This client or an ancestor is assigned to this user, so user is authorized
                    if ClientUser.objects.filter(user=request.user, client__is_active=True, client__id__in=client.ancestors).exists():
                        return client
                    # A previously selected client is no longer authorized for this user, so remove it from the session
                    # and return the results of get_first_authorized_client()
                    logger.info(f'Selected client {client} no longer valid for {request.user}')
                    del request.session['selected_client_id']
                    return self.get_first_authorized_client(request)
                except Client.DoesNotExist:
                    return self.get_first_authorized_client(request)
            else:
                return self.get_first_authorized_client(request)
        except Exception as e:
            logger.info(e)
            return None

    def get_first_authorized_client(self, request):
        client_user = ClientUser.objects.filter(user=request.user, client__is_active=True).first()
        if client_user:
            request.session['selected_client_id'] = client_user.client.id
            return client_user.client
        return None

    def __call__(self, request):
        request.selected_client = self.get_selected_client(request)
        return self.get_response(request)


class PermissionsMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    # def is_authorized_for_client(self, user, client):
    #     if not client:
    #         return False
    #     if user.is_admin:
    #         return True
    #     return ClientUser.objects.filter(user=user, client__is_active=True, client__id__in=client.ancestors).exists()

    def __call__(self, request):
        resolved = resolve(request.path_info)
        if resolved.url_name == 'sign-out':
            return self.get_response(request)

        if request.user.is_authenticated:
            if resolved.app_name == 'api' and not request.user.is_admin:
                logger.info(f'{request.user} not authorized for api.')
                raise PermissionDenied
            if resolved.app_name == 'mgmt' and not request.user.is_admin:
                logger.info(f'{request.user} not authorized for mgmt.')
                raise PermissionDenied
            if resolved.app_name == 'client' and not request.user.is_authorized_for_client(request.selected_client):
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


class LogCsrfMiddleware(MiddlewareMixin):

    def process_request(self, request):
        try:
            csrf_token = request.POST.get('csrfmiddlewaretoken')
            if csrf_token:
                logger.info(f'{request.method} {csrf_token}')
        except Exception as exc:
            logger.warning(exc)
        return None