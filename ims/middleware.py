from django.http import HttpResponseRedirect
from django.conf import settings
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.contrib.auth import logout
from re import compile

from thinkpackage.urls import urlpatterns_mgmt, urlpatterns_api

import logging
logger = logging.getLogger(__name__)


EXEMPT_URLS = []
if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
    EXEMPT_URLS += [compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]

class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to view any page other
    than LOGIN_URL. Exemptions to this requirement can optionally be specified
    in settings via a list of regular expressions in LOGIN_EXEMPT_URLS (which
    you can copy from your urls.py).
    Requires authentication middleware and template context processors to be
    loaded. You'll get an error if they aren't.
    """
    def process_request(self, request):
        assert hasattr(request, 'user'), "The Login Required middleware\
 requires authentication middleware to be installed. Edit your\
 MIDDLEWARE_CLASSES setting to insert\
 'django.contrib.auth.middleware.AuthenticationMiddleware'. If that doesn't\
 work, ensure your TEMPLATE_CONTEXT_PROCESSORS setting includes\
 'django.core.context_processors.auth'."
        if not request.user.is_authenticated() or not request.user.is_active:
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in EXEMPT_URLS):
                if path.startswith('mgmt/'):
                    return HttpResponseRedirect(reverse_lazy('mgmt-two_factor:login'))
                if path.startswith('client/'):
                    return HttpResponseRedirect(reverse_lazy('client-two_factor:login'))
#                return HttpResponseRedirect(settings.LOGIN_URL)


class PermissionsMiddleware:

    def process_request(self, request):
        path = request.path_info.lstrip('/')
        if not any(m.match(path) for m in EXEMPT_URLS):
            if request.user.is_authenticated() and path.startswith('mgmt/') and not request.user.is_admin:
                raise PermissionDenied
            if request.user.is_authenticated() and path.startswith('client/') and not request.user.is_authorized_for_client(request):
                logout(request)
                return HttpResponseRedirect(reverse_lazy('client-two_factor:login'))
