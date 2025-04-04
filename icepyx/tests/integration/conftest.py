import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_earthdata_env():
    if "EARTHDATA_USERNAME" not in os.environ:
        os.environ["EARTHDATA_USERNAME"] = "icepyx_devteam"
    else:
        print(f"Using EARTHDATA_USERNAME: {os.environ['EARTHDATA_USERNAME']}")
    if "EARTHDATA_PASSWORD" not in os.environ:  # consider adding password too
        print("Warning: EARTHDATA_PASSWORD not set. Tests will fail")
