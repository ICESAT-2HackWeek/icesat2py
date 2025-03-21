import os
from unittest import mock

import pytest


# PURPOSE: mock environmental variables
@pytest.fixture(scope="session", autouse=True)
def mock_settings_env_vars():
    with mock.patch.dict(
        "os.environ",
        {
            "EARTHDATA_USERNAME": "icepyx_devteam",
            "EARTHDATA_PASSWORD": "fake_earthdata_password",
            "EARTHDATA_EMAIL": "icepyx.dev@gmail.com",
        },
    ):
        yield


@pytest.fixture(scope="session")
def username():
    return os.environ.get("EARTHDATA_USERNAME")


@pytest.fixture(scope="session")
def password():
    return os.environ.get("EARTHDATA_PASSWORD")


@pytest.fixture(scope="session")
def email():
    return os.environ.get("EARTHDATA_EMAIL")


# This pollutes the environment with the test user's credentials

# def pytest_configure(config):
#     # append to netrc file and set permissions level
#     args = ("icepyx_devteam", "urs.earthdata.nasa.gov", os.getenv("NSIDC_LOGIN"))
#     netrc_file = os.path.join(os.path.expanduser("~"), ".netrc")
#     with open(netrc_file, "a+") as f:
#         f.write("machine {1} login {0} password {2}\n".format(*args))
#         os.chmod(netrc_file, 0o600)
