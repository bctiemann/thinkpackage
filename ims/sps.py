import requests
from redis import BlockingConnectionPool
from redis.client import Redis

from django.conf import settings

import logging
logger = logging.getLogger(__name__)


REDIS_KEY = 'sps_api_token'


class SPSService(object):

    TOKEN_URL = 'https://auth.spscommerce.com/oauth/token'
    TRANSACTION_URL = 'https://api.spscommerce.com/transactions/v2/'
    AUTH_CHECK_URL = 'https://api.spscommerce.com/auth-check'

    def __init__(self, *args, **kwargs):
        self.redis_client = Redis(connection_pool=BlockingConnectionPool())
        saved_token = self.redis_client.get(REDIS_KEY)
        if saved_token:
            self.token = saved_token.decode()
        else:
            self.token = self.get_token()

    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.token}'
        }

    def refresh_token(self):
        self.redis_client.delete(REDIS_KEY)
        self.token = self.get_token()

    def get_token(self):
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.SPS_APP_ID,
            "client_secret": settings.SPS_APP_SECRET,
            "audience": "api://api.spscommerce.com/"
        }
        response = requests.post(self.TOKEN_URL, data=payload)
        response.raise_for_status()
        result = response.json()
        self.redis_client.set(REDIS_KEY, value=result.get('access_token'), ex=result.get('expires_in'))
        return result.get('access_token')

    def auth_check(self):
        response = requests.get(self.AUTH_CHECK_URL, headers=self.get_headers())
        response.raise_for_status()
        logger.info('Auth successful.')

    def create_transaction(self, binary_data):
        transaction_url = f'{self.TRANSACTION_URL}'
        response = requests.post(transaction_url, data=binary_data, headers=self.get_headers())
        # response.raise_for_status()
        result = response.json()
        print(result)