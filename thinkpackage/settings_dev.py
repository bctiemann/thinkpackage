try:
    from settings_common import *
except ImportError:
    pass


#DEBUG = False

SERVER_HOST = 'thinkpackage.lionwire.com'
SERVER_URL_PREFIX = 'http://'
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
MEDIA_URL = '/media/'

LOG_DIR = '/usr/local/www/thinkpackage-dj/logs'
LOGGING['handlers']['logfile']['filename'] = LOG_DIR + '/django.log'

TWO_FACTOR_SMS_GATEWAY = 'two_factor.gateways.fake.Fake'

#EMAIL_HOST = 'mail.lionking.org'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

SUPPORT_EMAIL = 'btman@mac.com'
SITE_EMAIL = 'btman@mac.com'
DELIVERY_EMAIL = 'btman@mac.com'
COMPANY_PHONE_NUMBER = '(866) 111-2222'

CELERY_BROKER_URL = os.environ['CELERY_BROKER_URL']

