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
    PROCESSING_REPORTS_URL = 'https://api.spscommerce.com/transactions/v4/file-processing-reports'

    def __init__(self, *args, **kwargs):
        self.redis_client = Redis(connection_pool=BlockingConnectionPool())
        saved_token = self.redis_client.get(REDIS_KEY)
        if saved_token:
            self.token = saved_token.decode()
        else:
            self.token = self._get_token()

    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.token}'
        }

    def _refresh_token(self):
        self.redis_client.delete(REDIS_KEY)
        self.token = self._get_token()

    def _get_token(self):
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
        response = requests.get(self.AUTH_CHECK_URL, headers=self._get_headers())
        response.raise_for_status()
        logger.info('Auth successful.')

    def get_transaction_url(self, file_path='', file_key=''):
        transaction_url = f'{self.TRANSACTION_URL}'
        if file_path:
            transaction_url += f'{file_path}/'
        transaction_url += file_key
        return transaction_url

    def create_transaction(self, binary_data, file_path='', file_key=''):
        transaction_url = self.get_transaction_url(file_path, file_key)
        response = requests.post(transaction_url, data=binary_data, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def get_transaction(self, file_path='', file_key=''):
        transaction_url = self.get_transaction_url(file_path, file_key)
        response = requests.get(transaction_url, headers=self._get_headers())
        response.raise_for_status()
        return response.content

    def list_transactions(self, file_path='', limit=None):
        transaction_url = self.get_transaction_url(file_path)
        transaction_url += '*'
        params = {
            'limit': limit,
        }
        response = requests.get(transaction_url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def delete_transaction(self, file_path='', file_key=''):
        transaction_url = self.get_transaction_url(file_path, file_key)
        response = requests.delete(transaction_url, headers=self._get_headers())
        response.raise_for_status()
        return response.content

    def procesing_reports(self, page_number=None, page_size=None, start_date_time=None, end_date_time=None):
        '''
        :param page_number: int
        :param page_size: int
        :param start_date_time: datetime in ISO format (2016-06-23T09:07:21), i.e. from datetime.isoformat()
        :param end_date_time: datetime in ISO format (2016-06-23T09:07:21), i.e. from datetime.isoformat()
        :return: json
        '''
        url = self.PROCESSING_REPORTS_URL
        params = {
            'pageNumber': page_number,
            'pageSize': page_size,
            'startDateTime': start_date_time,
            'endDateTime': end_date_time,
        }
        response = requests.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json()