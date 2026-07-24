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


RGW_ADMIN_BUCKET_RESPONSE = {
    "bucket": "empty-bucket",
    "owner": "user1",
    "zonegroup": "default",
    "marker": "",
    "id": "bucket-id",
    "bucket_quota": {},
    "mtime": "2026-01-01T00:00:00.000000Z",
}


# Some buckets include these (and more) fields, we intentionally do not deserialize them as they are not needed.
# They have been serialized in earlier versions of rgw-admin.
RGW_ADMIN_BUCKET_UNUSED_FIELDS = {"master_ver": "0", "ver": "0", "max_marker": ""}


@pytest.mark.parametrize(
    ("usage", "unused_fields", "expected_size_kb", "expected_num_objects"),
    [
        pytest.param({}, {}, 0, 0, id="empty-usage"),
        pytest.param(None, {}, 0, 0, id="missing-usage"),
        pytest.param(
            {"rgw.main": {"size_kb_actual": 512, "size_kb": 1024, "num_objects": 3}},
            {},
            1024,
            3,
            id="with-usage",
        ),
        pytest.param({}, RGW_ADMIN_BUCKET_UNUSED_FIELDS, 0, 0, id="with-unused-fields"),
        pytest.param(
            {"rgw.main": {"size_kb_actual": 512, "size_kb": 1024, "num_objects": 3}},
            RGW_ADMIN_BUCKET_UNUSED_FIELDS,
            1024,
            3,
            id="with-usage-and-unused-fields",
        ),
    ],
)
def test_list_bucket_stats(
    session_request_mock: Mock,
    admin_client: AdminClient,
    usage: dict[str, object] | None,
    unused_fields: dict[str, str],
    expected_size_kb: int,
    expected_num_objects: int,
) -> None:
    bucket_response = {**RGW_ADMIN_BUCKET_RESPONSE, **unused_fields}
    if usage is not None:
        bucket_response["usage"] = usage
    session_request_mock().json.return_value = [bucket_response]

    buckets = admin_client.list_bucket_stats(user_id="user1")

    assert session_request_mock.call_args == call(
        "GET",
        "http://example.com/bucket",
        params={"stats": True, "uid": "user1"},
        data=None,
        allow_redirects=True,
    )
    assert len(buckets) == 1
    bucket = buckets[0]
    assert bucket.name == "empty-bucket"
    assert bucket.owner == "user1"
    assert bucket.size_kb == expected_size_kb
    assert bucket.num_objects == expected_num_objects
    if usage:
        assert bucket.size["rgw.main"].num_objects == expected_num_objects
    else:
        assert bucket.size == {}
