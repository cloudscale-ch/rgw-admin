from datetime import datetime, timedelta
from urllib.parse import urljoin, urlsplit

from django.utils import timezone
from botocore.auth import HmacV1Auth
from botocore.credentials import ReadOnlyCredentials
from requests.auth import AuthBase
import requests


class S3Auth(AuthBase):
    def __init__(self, access_key, secret_key):
        self._hmac_auth = HmacV1Auth(
            ReadOnlyCredentials(access_key, secret_key, None))

    def __call__(self, request):
        signature = self._hmac_auth.get_signature(
            request.method,
            urlsplit(request.url),
            request.headers)

        request.headers['Authorization'] = 'AWS {}:{}'.format(
            self._hmac_auth.credentials.access_key,
            signature)

        return request


class HttpError(Exception):
    def __init__(self, response):
        if response.content:
            # In case of 400 status_codes you get a json return that has an
            # attribute called 'Code'. All the other information is usually
            # useless.
            message = response.json()['Code']
        else:
            message = 'HTTP ' + str(response.status_code)
        super().__init__(message)
        self.response = response


class AdminClient:
    def __init__(self, url, access_key, secret_key):
        self._url = url
        self._auth = S3Auth(access_key, secret_key)

    def _request(self, method, path, *, params=None, data=None):
        url = urljoin(self._url, path)

        response = getattr(requests, method)(
            url,
            auth=self._auth,
            params=params,
            data=data,
            verify=False
        )

        if response.status_code >= 400:
            raise HttpError(response)
        response.raise_for_status()

        if method == 'delete':
            assert response.content == b''
            return

        return response.json()

    def _get(self, path, **kwargs):
        return self._request('get', path, **kwargs)

    def _post(self, path, **kwargs):
        return self._request('post', path, **kwargs)

    def _put(self, path, **kwargs):
        return self._request('put', path, **kwargs)

    def _delete(self, path, **kwargs):
        self._request('delete', path, **kwargs)

    def list_user_ids(self):
        return self._get('metadata/user')

    def get_user(self, user_id):
        return self._get('user', params={'uid': user_id})

    def get_bucket_info(self):
        return self._get(
            'bucket',
            params={
                'stats': True})

    def delete_user(self, user_id):
        return self._delete(
            'user',
            params=dict(
                uid=user_id,
            )
        )

    def update_user(self, user_id, email):
        return self._put(
            'user',
            params={
                'uid': user_id,
                'display-name': 'ffooo',
                'email': email})

    def create_user(self, user_id, display_name, *, user_caps={}):
        user_caps_str = ';'.join(
            '{}={}'.format(cap, ','.join(rights))
            for cap, rights in user_caps.items())

        #x = User.from_dict(dict(a='asdf'))
        #print(x)

        return self._put(
            'user',
            params={
                'uid': user_id,
                'display-name': display_name,
                'user-caps': user_caps_str})

    def get_usage(self, user_id, start: datetime):
        end = start + timedelta(hours=5)

        return self._get(
            'usage',
            params={
                'uid': user_id,
                'start': start.astimezone(timezone.utc).isoformat(' '),
                # 'end': end.astimezone(timezone.utc).isoformat(' '),
                'show-summary': False})
