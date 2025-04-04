import os
from unittest import mock
from unittest.mock import MagicMock

import pytest


# PURPOSE: mock environmental variables
@pytest.fixture(scope="session", autouse=True)
def mock_settings_env_vars():
    with mock.patch.dict(
        "os.environ",
        {
            "EARTHDATA_USERNAME": "icepyx_devteam",
            "EARTHDATA_EMAIL": "icepyx.dev@gmail.com",
        },
    ):
        yield


@pytest.fixture(autouse=True)
def mock_harmony_api(monkeypatch):
    """Globally mock HarmonyApi initialization and authentication."""
    mock_api = MagicMock()

    # Mock the HarmonyApi constructor
    def mock_harmony_init(self):
        self.harmony_client = MagicMock()
        self.get_capabilities = MagicMock(return_value={})

    # Apply the mock to the actual class
    monkeypatch.setattr("icepyx.core.query.HarmonyApi.__init__", mock_harmony_init)

    # Mock any methods that make external calls
    mock_api.place_order.return_value = "mock_job_id"
    monkeypatch.setattr("icepyx.core.query.HarmonyApi", mock_api)


@pytest.fixture(scope="session")
def username():
    return os.environ.get("EARTHDATA_USERNAME")


@pytest.fixture(scope="session")
def password():
    return os.environ.get("EARTHDATA_PASSWORD")


@pytest.fixture(scope="session")
def email():
    return os.environ.get("EARTHDATA_EMAIL")
