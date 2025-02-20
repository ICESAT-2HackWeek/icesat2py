from unittest.mock import patch

import pytest

from icepyx.core.variables import Variables, list_of_dict_vals


@pytest.mark.parametrize(
    "input_dict, expected",
    [
        ({}, []),
        ({"a": [1, 2, 3], "b": [4, 5, 6]}, [1, 2, 3, 4, 5, 6]),
        ({"a": [1, 2, 3, 4, 5, 6], "b": []}, [1, 2, 3, 4, 5, 6]),
        ({"a": [1], "b": [2], "c": [3], "d": [4]}, [1, 2, 3, 4]),
        ({"a": [1], "b": [1], "c": [1], "d": [1]}, [1, 1, 1, 1]),
        (
            {
                "sc_orient": ["orbit_info/sc_orient"],
                "data_start_utc": ["ancillary_data/data_start_utc"],
                "data_end_utc": ["ancillary_data/data_end_utc"],
                "h_li": ["gt1l/land_ice_segments/h_li"],
                "latitude": ["gt1l/land_ice_segments/latitude"],
                "longitude": ["gt1l/land_ice_segments/longitude"],
            },
            [
                "orbit_info/sc_orient",
                "ancillary_data/data_start_utc",
                "ancillary_data/data_end_utc",
                "gt1l/land_ice_segments/h_li",
                "gt1l/land_ice_segments/latitude",
                "gt1l/land_ice_segments/longitude",
            ],
        ),
    ],
)
def test_list_of_dict_vals(input_dict, expected):
    assert list_of_dict_vals(input_dict) == expected


def test_list_of_dict_vals_old():
    testdict = {
        "sc_orient": ["orbit_info/sc_orient"],
        "data_start_utc": ["ancillary_data/data_start_utc"],
        "data_end_utc": ["ancillary_data/data_end_utc"],
        "h_li": ["gt1l/land_ice_segments/h_li"],
        "latitude": ["gt1l/land_ice_segments/latitude"],
        "longitude": ["gt1l/land_ice_segments/longitude"],
    }

    obs = list_of_dict_vals(testdict)
    exp = [
        "orbit_info/sc_orient",
        "ancillary_data/data_start_utc",
        "ancillary_data/data_end_utc",
        "gt1l/land_ice_segments/h_li",
        "gt1l/land_ice_segments/latitude",
        "gt1l/land_ice_segments/longitude",
    ]

    assert obs == exp


def test_variables():
    with pytest.raises(TypeError):
        Variables()


def test_variable_path_and_product():
    with pytest.raises(TypeError):
        Variables(path="path", product="product")


def test_variable_mock_path():
    """
    Create a mock val.check_s3bucket(path) so it always returns path.
    """
    with (
        patch(
            "icepyx.core.validate_inputs.check_s3bucket", side_effect=lambda path: path
        ),
        patch(
            "icepyx.core.is2ref.extract_product",
            side_effect=lambda path, auth: f"prod: {path}, {auth}",
        ),
        patch(
            "icepyx.core.is2ref.extract_version",
            side_effect=lambda path, auth: f"vers: {path}, {auth}",
        ),
    ):
        variables = Variables(path="path")
        assert variables.path == "path"
        assert variables.product == "prod: path, None"
        assert variables.version == "vers: path, None"


def test_variable_mock_product():
    """
    Create a mock val.check_s3bucket(product) so it always returns product.
    """
    with (
        patch(
            "icepyx.core.validate_inputs.check_s3bucket",
            side_effect=lambda product: product,
        ),
        patch(
            "icepyx.core.validate_inputs.prod_version",
            side_effect=lambda product, auth: f"prod_version: {product}, {auth}",
        ),
        patch(
            "icepyx.core.is2ref._validate_product",
            side_effect=lambda product: True,
        ),
        patch(
            "icepyx.core.is2ref.latest_version",
            side_effect=lambda product: f"vers: {product}",
        ),
    ):
        variables = Variables(product="product")
        assert variables.product == "product"
        assert variables.path == "prod: product, None"
        assert variables.version == "vers: product, None"
