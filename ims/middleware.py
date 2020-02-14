from django.http import HttpResponseRedirect
from django.conf import settings
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.contrib.auth import logout
from re import compile

from ims.models import Client, ClientUser

import logging
logger = logging.getLogger(__name__)


EXEMPT_URLS = []
if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
    EXEMPT_URLS += [compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]

class LoginRequiredMiddleware(object):
    """
    Middleware that requires a user to be authenticated to view any page other
    than LOGIN_URL. Exemptions to this requirement can optionally be specified
    in settings via a list of regular expressions in LOGIN_EXEMPT_URLS (which
    you can copy from your urls.py).
    Requires authentication middleware and template context processors to be
    loaded. You'll get an error if they aren't.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        assert hasattr(request, 'user'), "The Login Required middleware\
 requires authentication middleware to be installed. Edit your\
 MIDDLEWARE_CLASSES setting to insert\
 'django.contrib.auth.middleware.AuthenticationMiddleware'. If that doesn't\
 work, ensure your TEMPLATE_CONTEXT_PROCESSORS setting includes\
 'django.core.context_processors.auth'."
        if not request.user.is_authenticated or not request.user.is_active:
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in EXEMPT_URLS):
                if path.startswith('mgmt/'):
                    return HttpResponseRedirect(reverse_lazy('mgmt:login'))
                if path.startswith('client/'):
                    return HttpResponseRedirect(reverse_lazy('client:login'))
                if path.startswith('warehouse/'):
                    return HttpResponseRedirect(reverse_lazy('warehouse:login'))
                if path.startswith('wapp/'):
                    return HttpResponseRedirect(reverse_lazy('warehouse_app:login'))
                if path.startswith('accounting/'):
                    return HttpResponseRedirect(reverse_lazy('accounting:login'))
#                return HttpResponseRedirect(settings.LOGIN_URL)

        return self.get_response(request)


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
        return ClientUser.objects.filter(user=user, client__id__in=client.ancestors).exists()

    def __call__(self, request):
        path = request.path_info.lstrip('/')
        if not any(m.match(path) for m in EXEMPT_URLS):
            if request.user.is_authenticated and path.startswith('mgmt/') and not request.user.is_admin:
                raise PermissionDenied
#            if request.user.is_authenticated and path.startswith('client/') and not self.is_authorized_for_client(request.user, self.get_selected_client(request)):
            if request.user.is_authenticated and path.startswith('client/') and not self.is_authorized_for_client(request.user, request.selected_client):
                logger.info('Unauthorized client login; logging out')
                logout(request)
                return HttpResponseRedirect(reverse_lazy('client:login'))
            if request.user.is_authenticated and path.startswith('warehouse/') and not request.user.is_warehouse:
                raise PermissionDenied
            if request.user.is_authenticated and path.startswith('accounting/') and not request.user.is_accounting:
                raise PermissionDenied

        return self.get_response(request)
