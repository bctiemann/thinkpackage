import requests
import json
from redis import BlockingConnectionPool
from redis.client import Redis

from django.conf import settings

from api.serializers import SPSOrderSerializer

import logging
logger = logging.getLogger(__name__)


REDIS_KEY = 'sps_api_token'
MIN_TTL = 300


class SPSService(object):

    TOKEN_URL = 'https://auth.spscommerce.com/oauth/token'
    TRANSACTION_URL = 'https://api.spscommerce.com/transactions/v2/'
    AUTH_CHECK_URL = 'https://api.spscommerce.com/auth-check'
    PROCESSING_REPORTS_URL = 'https://api.spscommerce.com/transactions/v4/file-processing-reports'

    def __init__(self, *args, **kwargs):
        self.redis_client = Redis(connection_pool=BlockingConnectionPool())

    def _check_token(self):
        ttl = self.redis_client.ttl(REDIS_KEY)
        if ttl < 0:
            self.token = self._get_token()
        elif ttl < MIN_TTL:
            self._refresh_token()
        else:
            saved_token = self.redis_client.get(REDIS_KEY)
            self.token = saved_token.decode()

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
        self._check_token()
        response = requests.get(self.AUTH_CHECK_URL, headers=self._get_headers())
        response.raise_for_status()
        logger.info('Auth successful.')

    def _get_transaction_url(self, file_path='', file_key=''):
        transaction_url = f'{self.TRANSACTION_URL}'
        if file_path:
            file_path = file_path.strip('/')
            transaction_url += f'{file_path}/'
        transaction_url += file_key
        return transaction_url

    def create_transaction(self, binary_data, file_path='', file_key=''):
        self._check_token()
        transaction_url = self._get_transaction_url(file_path, file_key)
        response = requests.post(transaction_url, data=binary_data, headers=self._get_headers())
        # response.raise_for_status()
        logger.info(f'Shipment payload {file_key} submitted as transaction with response code {response.status_code}')
        return response

    def get_transaction(self, file_path='', file_key=''):
        self._check_token()
        transaction_url = self._get_transaction_url(file_path, file_key)
        response = requests.get(transaction_url, headers=self._get_headers())
        response.raise_for_status()
        return response

    def list_transactions(self, file_path='', limit=None):
        self._check_token()
        transaction_url = self._get_transaction_url(file_path)
        transaction_url += '*'
        params = {
            'limit': limit,
        }
        response = requests.get(transaction_url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def delete_transaction(self, file_path='', file_key=''):
        self._check_token()
        transaction_url = self._get_transaction_url(file_path, file_key)
        response = requests.delete(transaction_url, headers=self._get_headers())
        response.raise_for_status()
        return response

    def processing_reports(self, page_number=None, page_size=None, start_date_time=None, end_date_time=None):
        '''
        :param page_number: int
        :param page_size: int
        :param start_date_time: datetime in ISO format (2016-06-23T09:07:21), i.e. from datetime.isoformat()
        :param end_date_time: datetime in ISO format (2016-06-23T09:07:21), i.e. from datetime.isoformat()
        :return: json
        '''
        self._check_token()
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

    def submit_shipment(self, shipment):
        serializer = SPSOrderSerializer(shipment)
        file_key = f'{settings.SPS_IN_PATH}/Shipment_{shipment.id}.json'
        self.create_transaction(json.dumps(serializer.data), file_key=file_key)
