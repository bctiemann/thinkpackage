try:
    from thinkpackage.settings_common import *
except ImportError:
    pass


DEBUG = False

SERVER_HOST = 'secure.thinkpackage.com'
SERVER_URL_PREFIX = 'https://'
SERVER_BASE_URL = '{0}{1}'.format(SERVER_URL_PREFIX, SERVER_HOST)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'think',
        'USER': 'think',
        'PASSWORD': os.environ['DB_PASS'],
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': 'SET character_set_connection=utf8mb4, collation_connection=utf8mb4_unicode_ci',
            'charset': 'utf8mb4',
        },
    },
    'legacy': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'tp',
        'USER': 'btman',
        'PASSWORD': os.environ['DB_PASS_LEGACY'],
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': 'SET character_set_connection=utf8mb4, collation_connection=utf8mb4_unicode_ci',
            'charset': 'utf8mb4',
        },
    },
}

STATIC_ROOT = '/usr/local/www/thinkpackage-dj/static_root'
MEDIA_ROOT = '/usr/local/www/thinkpackage-dj/media'
MEDIA_ROOT_LEGACY = '/usr/local/www/tp-data'
MEDIA_URL = '/media/'

LOG_DIR = '/usr/local/www/thinkpackage-dj/logs'
LOGGING['handlers']['logfile']['filename'] = LOG_DIR + '/django.log'
LOGGING['handlers']['auth_logfile']['filename'] = LOG_DIR + '/auth.log'

TWO_FACTOR_SMS_GATEWAY = 'two_factor.gateways.twilio.gateway.Twilio'
#TWO_FACTOR_SMS_GATEWAY = 'two_factor.gateways.fake.Fake'
TWO_FACTOR_CALL_GATEWAY = 'two_factor.gateways.twilio.gateway.Twilio'
TWILIO_ACCOUNT_SID = 'AC1e9dd3090c8ce40529da714a5e93c935'
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_CALLER_ID = '404-800-7627'

ADMINS = (
    ('Brian Tiemann', 'btman@mac.com'),
)

#EMAIL_HOST = 'mail.lionking.org'
EMAIL_HOST = 'blend.lionwire.com'
EMAIL_PORT = 25

SUPPORT_EMAIL = 'hello@thinkpackage.com'
SITE_EMAIL = 'info@thinkpackage.com'
DELIVERY_EMAIL = 'delivery@thinkpackage.com'
PO_EMAIL = 'po@thinkpackage.com'
COMPANY_PHONE_NUMBER = '(212) 229-0700'

CELERY_BROKER_URL = os.environ['CELERY_BROKER_URL']

DEFAULT_SHIPPER_ADDRESS = 1

GENERATE_QRCODE_IMAGES = False

ENFORCE_CLIENT_PASSWORD_EXPIRY = True