from datetime import datetime
from urllib.parse import urljoin, urlsplit, urlencode

from botocore.auth import HmacV1Auth
from botocore.credentials import ReadOnlyCredentials
from requests.auth import AuthBase
import requests
from requests.execeptions import ConnectionError

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
        self.message = message
        self.response = response


class AdminClient:
    def __init__(self, url, access_key, secret_key, *, verify_cert=True, redundant_url=None):
        self._url = url
        self._redundant_url = redundant_url
        """
        The redundant is simply here for high availability. It's used in case one
        server is dead.
        """
        self._session = session = requests.Session()

        session.verify = verify_cert
        session.auth = S3Auth(access_key, secret_key)

    def _request(self, method, path, schema=None, *, params=None, data=None):
        def _do_request(url):
            return getattr(self._session, method)(
                url,
                params=params,
                data=data,
            )

        url = urljoin(self._url, path)

        try:
            response = _do_request(url)
        except ConnectionError:
            if not self._redundant_url:
                raise
            url = urljoin(self._redundant_url, path)
            response = _do_request(url)

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

    def get_bucket_stats(self, name, *, user_id=None):
        """
        Returns None if the bucket doesn't exist.
        """
        raise NotImplementedError(
            "The bucket param below seems to be ignored. Therefore it's "
            "impossible to get this working."
        )
        json = self._get(
            'bucket',
            params={
                'uid': user_id,
                'bucket': name,
                'stats': True,
            }
        )
        # At this point there should be an entry.
        if not json:
            return None
        return serialization.Bucket.deserialize_from_python(json[0])

    def list_bucket_names(self, *, user_id=None):
        return self._list_bucket_stats(user_id, stats=False, serializer=None)

    def list_bucket_stats(self, *, user_id=None):
        return self._list_bucket_stats(user_id)

    def _list_bucket_stats(self, user_id=None, stats=True, serializer=serialization.BucketList):
        return self._get(
            'bucket',
            serializer,
            params={
                'uid': user_id,
                'stats': stats,
            }
        )

    def delete_bucket(self, name, purge_data=False):
        return self._delete(
            'bucket',
            params={
                'bucket': name,
                'purge-objects': purge_data
            }
        )

    def delete_user(self, user_id, purge_data=True):
        return self._delete(
            'user',
            params={
                'uid': user_id,
                'purge-data': purge_data
            }
        )

    def update_user(self, user_id, *, display_name=None):
        params = {'uid': user_id}
        if display_name is not None:
            params['display-name'] = display_name

        return self._post(
            'user',
            serialization.User,
            params=params
        )

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

    def generate_new_secret_key(self, user_id, access_key):
        # The url for keys is `user?key`, which makes no sense.
        dct = {'uid': user_id, 'access-key': access_key}
        params = 'key&' + urlencode(dct)
        return self._put(
            'user',
            serialization.KeyEntryList,
            params=params
        )
