"""
WSGI config for thinkpackage project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os, sys
from django.core.wsgi import get_wsgi_application

env_variables_to_pass = [
    'BASE_PATH',
    'SECRET_KEY',
    'DB_PASS',
    'DB_PASS_LEGACY',
    'TWILIO_AUTH_TOKEN',
    'DJANGO_SETTINGS_MODULE',
    'WKHTMLTOPDF_BIN',
    'CELERY_BROKER_URL',
    'LOG_AUTH',
    'SPS_APP_ID',
    'SPS_APP_SECRET',
]

os.environ["DJANGO_SETTINGS_MODULE"] = "thinkpackage.settings_prod"

django_application = None

def application(environ, start_response):
    global django_application
    if django_application is None:
        # pass the WSGI environment variables on through to os.environ
        for var in env_variables_to_pass:
            os.environ[var] = environ.get(var, '')
        django_application = get_wsgi_application()
    return django_application(environ, start_response)


