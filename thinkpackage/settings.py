import os
import yaml
from concurrent_log_handler import ConcurrentRotatingFileHandler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'dummy'

DEBUG = False

ALLOWED_HOSTS = [
    'thinkpackage.lionking.org',
    'thinkpackage.lionwire.com',
    'thinkpackage.grotto11.com',
    'secure.thinkpackage.com',
]

SERVER_BASE_URL = 'https://secure.thinkpackage.com'


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

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'ims.middleware.LoginRequiredMiddleware',
    'ims.middleware.SelectedClientMiddleware',
    'ims.middleware.PermissionsMiddleware',
    'ims.middleware.SiteClosedMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'two_factor.middleware.threadlocals.ThreadLocals',
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}

ROOT_URLCONF = 'thinkpackage.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


#LOGIN_URL = 'mgmt-two_factor:login'
LOGIN_URL = 'two_factor:login'
# LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/account/two_factor/'

AUTH_EXEMPT_ROUTES = (
    'login',
    'pallet-code',
    'product-code',
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
STATIC_ROOT = '/usr/local/www/thinkpackage-dj/static_root'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/usr/local/www/thinkpackage-dj/media'
MEDIA_ROOT_LEGACY = '/usr/local/www/tp-data'

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
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'logfile': {
            'level': 'INFO',
            'filters': [],
            'class': 'logging.handlers.ConcurrentRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024*1024*64, # 64mb
            'backupCount': 5,
            'formatter': 'colored',
        },
        'auth_logfile': {
            'level': 'INFO',
            'filters': [],
            'class': 'logging.handlers.ConcurrentRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'auth.log'),
            'maxBytes': 1024 * 1024 * 64,  # 64mb
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
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        # Log all app logger messages to the central logfile
        '': {
            'handlers': ['logfile'],
            'level': 'INFO',
            'propagate': True,
        },
        'auth': {
            'handlers': ['auth_logfile'],
            'level': 'INFO',
            'propagate': False,
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

ADMINS = (
    ('Brian Tiemann', 'btman@mac.com'),
)

SITE_CLOSED = False

TWO_FACTOR_SMS_GATEWAY = 'two_factor.gateways.twilio.gateway.Twilio'
TWO_FACTOR_CALL_GATEWAY = 'two_factor.gateways.twilio.gateway.Twilio'
TWILIO_CALLER_ID = '404-800-7627'

# Celery
#CELERY_TASK_SERIALIZER = 'pickle'
#CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_RESULT_BACKEND = 'rpc://'
#CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_BROKER_URL = 'redis://localhost:6379'

CSRF_FAILURE_VIEW = 'ims.views.csrf_failure'

# Email config
EMAIL_HOST = 'blend.lionwire.com'
EMAIL_PORT = 25

COMPANY_NAME = 'THINK[PACKAGE]'
COMPANY_PHONE_NUMBER = '(212) 229-0700'
SUPPORT_EMAIL = 'hello@thinkpackage.com'
SITE_EMAIL = 'info@thinkpackage.com'
DELIVERY_EMAIL = 'delivery@thinkpackage.com'
CLAIMS_EMAIL = 'claims@thinkpackage.com'
PO_EMAIL = 'po@thinkpackage.com'
NO_REPLY_EMAIL = 'no-reply@thinkpackage.com'
FRONTSITE_URL = 'http://thinkpackage.com'
BCC_EMAIL = None

INFINITE_SCROLL_PAGE_SIZE = 30

COUNTRIES_FIRST = ['US', 'CA']
# COUNTRIES_FIRST_BREAK = '(Select country)'

DEFAULT_SHIPPER_ADDRESS = None

PASSWORD_EXPIRE_DAYS = 90
PASSWORD_PROMPT_REAPPEAR_DAYS = 1
ENFORCE_CLIENT_PASSWORD_EXPIRY = True

GENERATE_QRCODE_IMAGES = False

ALLOW_BYPASS_WAREHOUSE_SCAN = False

LOG_AUTH = False

# Workaround Safari email click-tracking issue for password reset links
CSRF_COOKIE_SAMESITE = None
SESSION_COOKIE_SAMESITE = None

# SPS Commerce / Netsuite integration
SPS_APP_ID = None
SPS_APP_SECRET = None
SPS_IN_PATH = ''
SPS_ENABLE = False
SPS_SUBMIT_ON_CREATE = True
SPS_SUBMIT_ON_SHIP = False

WKHTMLTOPDF_BIN = '/usr/local/bin/wkhtmltopdf'


# Local overrides from env.yaml
with open(os.path.join(BASE_DIR, 'env.yaml')) as f:
    local_settings = yaml.load(f, Loader=yaml.FullLoader)
globals().update(local_settings)

os.environ['WKHTMLTOPDF_BIN'] = WKHTMLTOPDF_BIN
