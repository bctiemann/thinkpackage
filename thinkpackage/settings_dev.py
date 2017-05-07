try:
    from settings_common import *
except ImportError:
    pass


#DEBUG = False

SERVER_HOST = 'thinkpackage.lionking.org'
SERVER_URL_PREFIX = 'http://'
SERVER_BASE_URL = '{0}{1}'.format(SERVER_URL_PREFIX, SERVER_HOST)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'thinkpackage',
        'USER': 'thinkpackage',
        'PASSWORD': os.environ['DB_PASS'],
        'HOST': '10.0.0.2',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': 'SET character_set_connection=utf8mb4, collation_connection=utf8mb4_unicode_ci',
            'charset': 'utf8mb4',
        },
    },
}

TWO_FACTOR_SMS_GATEWAY = 'two_factor.gateways.fake.Fake'

#EMAIL_HOST = 'mail.lionking.org'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

SUPPORT_EMAIL = 'btman@mac.com'

