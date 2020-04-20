try:
    from thinkpackage.settings_common import *
except ImportError:
    pass


#DEBUG = False

SERVER_HOST = 'localhost:8000'
SERVER_URL_PREFIX = 'http://'
SERVER_BASE_URL = '{0}{1}'.format(SERVER_URL_PREFIX, SERVER_HOST)

ALLOWED_HOSTS = [
    'localhost',
]

STATIC_ROOT = '/Users/brian.tiemann/Development/thinkpackage-dj/static_root'

MEDIA_ROOT = '/Users/brian.tiemann/Development/thinkpackage-dj/media'
MEDIA_ROOT_LEGACY = '/Users/brian.tiemann/Development/thinkpackage-dj/old_media'
MEDIA_URL = '/media/'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
