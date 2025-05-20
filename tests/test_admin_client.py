from unittest.mock import Mock
from unittest.mock import call

import pytest
from pytest import MonkeyPatch
from requests import Session

from rgw_admin import AdminClient

rgw_admin_user_response_json = dict(
    display_name="display-name",
    user_id="123",
    email="hello@cloudscale.ch",
    keys=[],
    suspended=0,
    max_buckets=100,
    tenant="tenant",
    swift_keys=None,
    caps=None,
    subusers=None,
)


@pytest.fixture
def session_request_mock(monkeypatch: MonkeyPatch) -> Mock:
    monkeypatch.setattr(Session, "request", request_mock := Mock())
    request_mock().status_code = 200
    request_mock().json.return_value = {}

    return request_mock


@pytest.fixture
def admin_client(session_request_mock: Mock) -> AdminClient:
    return AdminClient("http://example.com", "access-key", "secret-key")


def test_get_user(session_request_mock: Mock, admin_client: AdminClient) -> None:
    session_request_mock().json.return_value = rgw_admin_user_response_json

    admin_client.get_user("my-user-id")
    assert session_request_mock.call_args == call(
        "GET",
        "http://example.com/user",
        params={"uid": "my-user-id"},
        data=None,
        allow_redirects=True,
    )

    admin_client.get_user(access_key="my-access-key")
    assert session_request_mock.call_args == call(
        "GET",
        "http://example.com/user",
        params={"access-key": "my-access-key"},
        data=None,
        allow_redirects=True,
    )
