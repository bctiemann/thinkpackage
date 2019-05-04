"""
Django settings for thinkpackage project.

Generated by 'django-admin startproject' using Django 1.9.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import sys
import datetime
from colorlog import ColoredFormatter
from cloghandler import ConcurrentRotatingFileHandler

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '*$1n5t3y-2=su!z0ijv9$gskc8+z%=tjo8vfp(qg6thxzr8z8m'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'thinkpackage.lionking.org',
    'thinkpackage.lionwire.com',
    'thinkpackage.grotto11.com',
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'rest_framework',
    'phonenumber_field',
    'django_tables2',
#    'django_filters',

    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',

    'ims',
    'mgmt',
    'client',
    'warehouse',
    'warehouse_app',
    'accounting',
    'api',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'ims.middleware.LoginRequiredMiddleware',
    'ims.middleware.SelectedClientMiddleware',
    'ims.middleware.PermissionsMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'two_factor.middleware.threadlocals.ThreadLocals',
]

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

ROOT_URLCONF = 'thinkpackage.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
#        'DIRS': ['templates',],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'ims.context_processors.settings_constants',
            ],
        },
    },
]

WSGI_APPLICATION = 'thinkpackage.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'ims.User'


#LOGIN_URL = 'mgmt-two_factor:login'
#LOGIN_URL = 'two_factor:login'
LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/account/two_factor/'

LOGIN_EXEMPT_URLS = (
    r'^recovery/',
    r'^mgmt/login/$',
    r'^client/$',
    r'^client/login/$',
    r'^warehouse/$',
    r'^warehouse/login/$',
#    r'^warehouse_app/$',
    r'^warehouse_app/login/$',
    r'^accounting/$',
    r'^accounting/login/$',
)

#LOGIN_URL = '/sign_in/'
#LOGIN_REDIRECT_URL = '/account/profile/'
#LOGOUT_REDIRECT_URL = '/'


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATICFILES_DIRS = ['static',]
STATIC_URL = '/static/'
# STATIC_ROOT = '/usr/local/www/django/thinkpackage/static_root'
# MEDIA_ROOT = '/usr/local/www/django/thinkpackage/media'
# MEDIA_URL = '/media/'

LOG_DIR = '/var/log/thinkpackage'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'datefmt' : "%d/%b/%Y %H:%M:%S",
            'format': "%(purple)s[%(asctime)s] %(cyan)s[%(name)s:%(lineno)s] %(log_color)s%(levelname)-4s%(reset)s %(white)s%(message)s"
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'logfile': {
            'level':'INFO',
            'filters': [],
            'class':'logging.handlers.ConcurrentRotatingFileHandler',
            'filename': LOG_DIR + '/django.log',
            'maxBytes': 1024*1024*64, # 64mb
            'backupCount': 5,
            'formatter': 'colored',
        },
        'console': {
            'level': 'DEBUG',
            'filters': [],
            'class': 'logging.StreamHandler',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        # Log all app logger messages to the central logfile
        '': {
            'handlers': ['logfile'],
            'level': 'INFO',
            'propagate': True,
        },
        # Log database diagnostics at WARN level
        'django.db.backends': {
            'level': 'WARN',
            'handlers': ['logfile'],
        },
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
    },
}

#PHONENUMBER_DB_FORMAT = 'NATIONAL'

#REST_FRAMEWORK = {
#    'DEFAULT_AUTHENTICATION_CLASSES': (
#        'rest_framework.authentication.BasicAuthentication',
#        'rest_framework.authentication.SessionAuthentication',
#    )
#}

# Celery
#CELERY_TASK_SERIALIZER = 'pickle'
#CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_RESULT_BACKEND = 'rpc://'
#CELERY_ACCEPT_CONTENT = ['pickle']


COMPANY_NAME = 'THINK[PACKAGE]'
COMPANY_PHONE_NUMBER = '(212) 229-0700'
SUPPORT_EMAIL = 'info@thinkpackage.com'
SITE_EMAIL = 'info@thinkpackage.com'
DELIVERY_EMAIL = 'delivery@thinkpackage.com'
FRONTSITE_URL = 'http://thinkpackage.com'

CLIENTACCESS_EMAIL = 'clientaccess@thinkpackage.com'

