from datetime import datetime
from urllib.parse import urljoin, urlsplit

from botocore.auth import HmacV1Auth
from botocore.credentials import ReadOnlyCredentials
from requests.auth import AuthBase
import requests

from rgw_admin import serialization


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
            try:
                message = response.json()['Code']
            except ValueError:
                message = 'HTTP ' + str(response.status_code)
        else:
            message = 'HTTP ' + str(response.status_code)
        super().__init__(message)
        self.response = response


class AdminClient:
    def __init__(self, url, access_key, secret_key, verify_cert=True):
        self._url = url
        self._auth = S3Auth(access_key, secret_key)
        self._access_key = access_key
        self._secret_key = secret_key
        self._verify_cert = verify_cert

    def _request(self, method, path, schema=None, *, params=None, data=None):
        url = urljoin(self._url, path)

        response = getattr(requests, method)(
            url,
            auth=self._auth,
            params=params,
            data=data,
            verify=self._verify_cert
        )

        if response.status_code >= 400:
            raise HttpError(response)
        response.raise_for_status()

        if method == 'delete':
            assert response.content == b''
            return

        json = response.json()
        if schema is None:
            return json

        return schema.deserialize_from_python(json)

    def _get(self, *args, **kwargs):
        return self._request('get', *args, **kwargs)

    def _post(self, *args, **kwargs):
        return self._request('post', *args, **kwargs)

    def _put(self, *args, **kwargs):
        return self._request('put', *args, **kwargs)

    def _delete(self, *args, **kwargs):
        self._request('delete', *args, **kwargs)

    def list_user_ids(self):
        return self._get('metadata/user')

    def get_user(self, user_id):
        return self._get('user', serialization.User, params={'uid': user_id})

    def get_bucket_info(self, name, *, user_id=None):
        return self._get(
            'bucket',
            serialization.Bucket,
            params={
                'uid': user_id,
                'bucket': name,
                'stats': True,
            }
        )

    def list_bucket_info(self, *, user_id=None):
        return self._get(
            'bucket',
            serialization.BucketList,
            params={
                'uid': user_id,
                'stats': True,
            }
        )

    def delete_bucket(self, name, purge_objects=False):
        return self._delete(
            'bucket',
            params={
                'bucket': name,
                'purge-objects': purge_objects
            }
        )

    def delete_user(self, user_id):
        return self._delete(
            'user',
            params=dict(
                uid=user_id,
            )
        )

    def update_user(self, user_id, display_name):
        return self._post(
            'user',
            serialization.User,
            params={
                'uid': user_id,
                'display-name': display_name
            })

    def create_user(self, user_id, display_name, *, user_caps={}):
        user_caps_str = ';'.join(
            '{}={}'.format(cap, ','.join(rights))
            for cap, rights in user_caps.items())

        return self._put(
            'user',
            serialization.User,
            params={
                'uid': user_id,
                'display-name': display_name,
                'user-caps': user_caps_str})

    def get_usage(self, user_id=None, start : int = None, end : int = None):
        assert start is None or isinstance(start, datetime), start
        assert end is None or isinstance(end, datetime), end
        return self._get(
            'usage',
            serialization.Usage,
            params={
                'uid': user_id,
                'start': start,
                'end': end,
                'show-summary': False})
