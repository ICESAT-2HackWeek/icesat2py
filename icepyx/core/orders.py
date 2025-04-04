from pathlib import Path
from typing import Any, Dict, Union

import earthaccess


class DataOrder:
    """
    A class representing an order for Harmony data processing.

    Attributes
    ----------
    job_id : str
        The ID of the Harmony job.
    type : str
        The type of order (e.g., "subset").
    granules : list
        A list of granules included in the order.
    harmony_client : object
        The Harmony API client used for interacting with the service.

    Methods
    -------
    id()
        Returns the job ID of the order.
    resume()
        Resumes the order if it has been paused due to exceeding granule limits.
    pause()
        Pauses the order.
    cancel()
        Cancels the order.
    status()
        Retrieves the status of the order.
    download_granules(path, overwrite=False)
        Downloads the granules associated with the order.
    download(path, overwrite=False)
        Downloads the granules, waiting until they are ready if necessary.
    """

    HARMONY_BASE_URL = "https://harmony.earthdata.nasa.gov/workflow-ui/"

    def __init__(self, job_id, type, granules, harmony_client):
        """
        Initialize a DataOrder object.

        Parameters
        ----------
        job_id : str
            The ID of the Harmony job.
        type : str
            The type of order (e.g., "subset").
        granules : list
            A list of granules included in the order.
        harmony_client : object
            The Harmony API client.
        """
        self.job_id = job_id
        self.harmony_api = harmony_client
        self.granules = granules
        self.type = type

    def __str__(self) -> str:
        return f"DataOrder(job_id={self.job_id}, type={self.type}, granules={self.granules})"

    def _repr_html_(self) -> str:
        # Create a link using the <a> tag
        status = self.status()
        link_html = f'<a target="_blank" href="{self.HARMONY_BASE_URL}{self.job_id}">View Details</a>'
        # Create a self-contained HTML table with a single row
        html = f"""
        <table border="1">
            <thead>
                <tr>
                    <th>Job ID</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{self.job_id}</td>
                    <td>{self.type}</td>
                    <td>{status["status"]}</td>
                    <td>{link_html}</td>
                </tr>
            </tbody>
        </table>
        """
        return html

    def __repr__(self) -> str:
        return self.__str__()

    def id(self) -> str:
        """
        Get the job ID of the order.

        Returns
        -------
        str
            The Harmony job ID.
        """
        return self.job_id

    def resume(self) -> Union[Dict[str, Any], None]:
        """
        Resume the order if it has been paused or is on a "preview" state.

        Returns
        -------
        dict or None
            The response from the Harmony API if the order is resumed, otherwise None.
        """
        if self.type == "subset":
            return self.harmony_api.resume_order(self.job_id)
        return None

    def skip_preview(self) -> Union[Dict[str, Any], None]:
        """
        Resume the order if it has been paused due to exceeding granule limits.

        Returns
        -------
        dict or None
            The response from the Harmony API if the order is resumed, otherwise None.
        """
        if self.type == "subset":
            return self.harmony_api.skip_preview(self.job_id)
        return None

    def pause(self) -> Union[Dict[str, Any], None]:
        """
        Pause the order.

        Returns
        -------
        dict or None
            The response from the Harmony API if the order is paused, otherwise None.
        """
        if self.type == "subset":
            return self.harmony_api.pause_order(self.job_id)
        return None

    def status(self) -> Dict[str, Any]:
        """
        Retrieve the status of the order.

        Returns
        -------
        dict
            A dictionary containing the order status and related metadata.
        """
        if self.type == "subset":
            status = self.harmony_api.check_order_status(self.job_id)
            # so users don't accidentally order again
            status.pop("request")
            status["order_url"] = self.HARMONY_BASE_URL + str(self.job_id)
            return status
        return {"status": "complete"}

    def download_granules(self, path, overwrite=False) -> Union[list, None]:
        """
        Download the granules for the order.

        Parameters
        ----------
        path : str or Path
            The directory where granules should be saved.
        overwrite : bool, optional
            Whether to overwrite existing files (default is False).
        Returns
        -------
        list or None
            A list of downloaded granules

        """
        return self.download(path, overwrite=overwrite)

    def download(self, path, overwrite=False) -> Union[list, None]:
        """
        Download the granules for the order, blocking until they are ready if necessary.

        Parameters
        ----------
        path : str or Path
            The directory where granules should be saved.
        overwrite : bool, optional
            Whether to overwrite existing files (default is False).

        Returns
        -------
        list or None
            A list of downloaded granules
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        if self.type == "subset":
            return self.harmony_api.download_granules(
                download_dir=str(path), overwrite=overwrite
            )
        else:
            return earthaccess.download(self.granules, local_path=path)
