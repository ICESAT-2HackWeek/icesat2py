import os

import pytest
import requests

from icepyx.core.auth import EarthdataAuthMixin


@pytest.fixture()
def auth_instance():
    """
    An EarthdatAuthMixin object for each of the tests. Default scope is function
    level, so a new instance should be created for each of the tests.
    """
    if os.environ.get("EARTHDATA_USERNAME") is None:
        print("Warning: EARTHDATA_USERNAME not set. Using default for testing.")
        os.environ["EARTHDATA_USERNAME"] = "icepyx_devteam"
    return EarthdataAuthMixin()


# Test that .session creates a session
def test_get_session(auth_instance):
    assert isinstance(auth_instance.session, requests.sessions.Session)


# Test that .s3login_credentials creates a dict with the correct keys
def test_get_s3login_credentials(auth_instance):
    assert isinstance(auth_instance.s3login_credentials, dict)
    expected_keys = {"accessKeyId", "secretAccessKey", "sessionToken", "expiration"}
    assert set(auth_instance.s3login_credentials.keys()) == expected_keys
