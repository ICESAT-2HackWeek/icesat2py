from unittest.mock import Mock, patch

from icepyx.core.query import DataOrder

# Mock the earthaccess module
earthaccess = Mock()


def test_status_subset():
    # Mock the harmony_client
    mock_harmony_client = Mock()
    mock_harmony_client.check_order_status.return_value = {"status": "processing"}

    # Create a DataOrder instance with type="subset"
    order = DataOrder(
        job_id=123,
        type="subset",
        granules=["granule1", "granule2"],
        harmony_client=mock_harmony_client,
    )

    # Call the status method
    result = order.status()

    # Verify the result and that the mock was called
    assert result == {"status": "processing"}
    mock_harmony_client.check_order_status.assert_called_once_with(123)


def test_status_non_subset():
    # Mock the harmony_client (not used in this case)
    mock_harmony_client = Mock()

    # Create a DataOrder instance with type="download"
    order = DataOrder(
        job_id=456,
        type="download",
        granules=["granule1", "granule2"],
        harmony_client=mock_harmony_client,
    )

    # Call the status method
    result = order.status()

    # Verify the result
    assert result == {"status": "complete"}
    mock_harmony_client.check_order_status.assert_not_called()


def test_download_subset():
    # Mock the harmony_client
    mock_harmony_client = Mock()
    mock_harmony_client.download_granules.return_value = "downloaded_subset"

    # Create a DataOrder instance with type="subset"
    order = DataOrder(
        job_id=123,
        type="subset",
        granules=["granule1", "granule2"],
        harmony_client=mock_harmony_client,
    )

    # Call the download method
    result = order.download("/fake/path", overwrite=True)

    # Verify the result and that the mock was called
    assert result == "downloaded_subset"
    mock_harmony_client.download_granules.assert_called_once_with(
        download_dir="/fake/path", overwrite=True
    )


@patch("earthaccess.download")  # Patch the earthaccess.download method
def test_download_non_subset(mock_earthaccess_download):
    # Mock the harmony_client (not used in this case)
    mock_harmony_client = Mock()

    # Mock the earthaccess.download method to return specific file paths
    mock_earthaccess_download.return_value = [
        "/fake/path/granule1.nc",
        "/fake/path/granule2.nc",
    ]

    # Create a DataOrder instance with type="download"
    order = DataOrder(
        job_id=456,
        type="download",
        granules=["granule1", "granule2"],
        harmony_client=mock_harmony_client,
    )

    # Call the download method
    result = order.download("/fake/path")

    # Verify the result and that the mock was called
    assert result == ["/fake/path/granule1.nc", "/fake/path/granule2.nc"]
    mock_earthaccess_download.assert_called_once_with(
        ["granule1", "granule2"], local_path="/fake/path"
    )
    mock_harmony_client.download_granules.assert_not_called()
