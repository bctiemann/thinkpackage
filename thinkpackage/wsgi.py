"""
WSGI config for thinkpackage project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os, sys
from django.core.wsgi import get_wsgi_application

env_variables_to_pass = [
    'SECRET_KEY',
    'DJANGO_SETTINGS_MODULE',
]

def application(environ, start_response):
    # pass the WSGI environment variables on through to os.environ
    for var in env_variables_to_pass:
        os.environ[var] = environ.get(var, '')
    return get_wsgi_application()(environ, start_response)
