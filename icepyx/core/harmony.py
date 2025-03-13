from concurrent.futures import as_completed
import datetime as dt
import json
from pathlib import Path
import time
from typing import Any, Dict, TypedDict, Union

from _icepyx_version import version as ipx_version
import harmony
import requests

from icepyx.core.auth import EarthdataAuthMixin

# Sometimes harmony has problems (e.g., 500 bad gateway) and we need to retry.
# 5 seconds seems like enough, but not always.
REQUEST_RETRY_INTERVAL_SECONDS: int = 5


class HarmonyTemporal(TypedDict):
    # TODO: these are optional. Harmony can take a start without a stop or a
    # stop without a start.
    start: dt.datetime
    stop: dt.datetime


class HarmonyApi(EarthdataAuthMixin):
    """
    A client for interacting with the NASA Harmony API.

    Attributes
    ----------
    harmony_client : harmony.Client
        The Harmony API client.
    job_ids : list of str
        List of job IDs that have been placed with the Harmony API.

    Methods
    -------
    get_capabilities(concept_id)
        Retrieves the capabilities of a given dataset.
    check_order_status(job_id)
        Checks the status of a submitted Harmony job.
    place_order(...)
        Submits an order to Harmony and waits for completion.
    download_granules(download_dir, overwrite)
        Downloads all granules associated with past orders.
    """

    def __init__(self):
        # initialize authentication properties
        self.ipx_version = ipx_version
        EarthdataAuthMixin.__init__(self)
        self.harmony_client = harmony.Client(
            auth=(
                self.auth.username,
                self.auth.password,
            ),
        )

        # List of job IDs that have been placed with the HarmonyApi
        self.job_ids = []

    def get_capabilities(self, concept_id: str) -> dict[str, Any]:
        """
        Retrieve the capabilities of a dataset given its concept ID.

        Parameters
        ----------
        concept_id : str
            The concept ID of the dataset.

        Returns
        -------
        dict
            A dictionary containing dataset capabilities.
        """
        capabilities_request = harmony.CapabilitiesRequest(collection_id=concept_id)
        response = self.harmony_client.submit(capabilities_request)
        return response

    def _place_order(
        self,
        concept_id: str,
        # These are optional subset parameters
        spatial: Union[harmony.BBox, str, harmony.WKT, None] = None,
        temporal: Union[HarmonyTemporal, None] = None,
        shape: Union[str, None] = None,
        granule_name: list[str] = [],
        skip_preview: bool = False,
    ) -> Any:
        """
        Submit an order to Harmony and wait for it to complete.

        Parameters
        ----------
        concept_id : str
            The concept ID of the dataset.
        spatial : harmony.BBox, str, harmony.WKT, or None, optional
            The spatial extent for the order.
        temporal : HarmonyTemporal or None, optional
            The temporal range for the order.
        shape : str or None, optional
            A spatial shape file for filtering.
        granule_name : list of str, optional
            Specific granule names to include in the order.
        skip_preview : bool, optional
            Whether to bypass preview mode if the order exceeds 300 granules.

        Returns
        -------
        str
            The Harmony job ID.
        """
        collection = harmony.Collection(id=concept_id)
        if spatial is not None and isinstance(spatial, str):
            spatial = harmony.WKT(spatial)

        params = {
            "collection": collection,
            "spatial": spatial,
            "temporal": temporal,
            # "skip_preview": skip_preview,
        }
        if skip_preview:
            params["skip_preview"] = skip_preview
        if granule_name:
            params["granule_name"] = granule_name

        request = harmony.Request(**params)

        if not request.is_valid():
            raise RuntimeError(
                f"Failed to create valid harmony request: {request.error_messages()}"
            )

        job_id = self.harmony_client.submit(request)
        label_req = harmony.AddLabelsRequest(
            labels=["icepyx", f"icepyx-{self.ipx_version}"], job_ids=[job_id]
        )
        self.harmony_client.submit(label_req)
        return job_id

    def check_order_status(self, job_id: str) -> dict[str, Any]:
        """
        Check the status of a submitted Harmony job.

        Parameters
        ----------
        job_id : str

        """

        retries = 3

        for retry_num in range(1, retries + 1):
            try:
                status = self.harmony_client.status(job_id)
                return status
            except requests.HTTPError as e:
                if retry_num >= retries:
                    raise e

                print(
                    f"Encountered HTTPError {e} while requesting job status"
                    f" for {job_id}. Retrying...{retry_num}/{retries}"
                )
                time.sleep(REQUEST_RETRY_INTERVAL_SECONDS)

        raise RuntimeError(f"Failed to get harmony order status for {job_id}")

    def resume_order(self, job_id: str) -> None:
        """
        Resume processing of an order that is paused.

        Parameters
        ----------
        job_id : str
            The ID of the Harmony job to resume.

        Returns
        -------
        dict
            A dictionary containing the order status and related metadata.
        """
        return self.harmony_client.resume(job_id)

    def pause_order(self, job_id: str) -> None:
        """
        Pauses an order that is currently processing.

        Parameters
        ----------
        job_id : str
            The ID of the Harmony job to resume.

        Returns
        -------
        dict
            A dictionary containing the order status and related metadata.
        """
        return self.harmony_client.pause(job_id)

    def skip_preview(self, job_id: str) -> Dict[str, Any]:
        """
        Resume processing of an order that is in the "PREVIEW" state.

        If a subsetting order exceeds 300 granules, Harmony places it in a paused state
        called "preview," where only a few granules are processed initially. This method
        resumes processing by first pausing and then resuming the order.

        Parameters
        ----------
        job_id : str
            The ID of the Harmony job to resume.

        Returns
        -------
        dict
            A dictionary containing the order status and related metadata.
        """
        status = self.check_order_status(job_id)
        if status["status"] == "paused" or status["status"] == "previewing":
            # we cannot skip after the facvt but pausing and resuming the order does the trick
            self.pause_order(job_id)
            self.resume_order(job_id)
            return self.check_order_status(job_id)
        else:
            return {"message": "Order is not in preview state."}

    def place_order(
        self,
        concept_id: str,
        # These are optional subset parameters
        spatial: Union[harmony.BBox, str, harmony.WKT, None] = None,
        temporal: Union[HarmonyTemporal, None] = None,
        shape: Union[str, None] = None,
        granule_name: list[str] = [],
        skip_preview: bool = False,
    ) -> Any:
        """
        Submit an order to Harmony and wait for it to complete.

        Parameters
        ----------
        concept_id : str
            The concept ID of the dataset.
        spatial : harmony.BBox, str, harmony.WKT, or None, optional
            The spatial extent for the order.
        temporal : HarmonyTemporal or None, optional
            The temporal range for the order.
        shape : str or None, optional
            A spatial shape file for filtering.
        granule_name : list of str, optional
            Specific granule names to include in the order.
        skip_preview : bool, optional
            Whether to bypass preview mode if the order exceeds 300 granules.

        Returns
        -------
        str
            The Harmony job ID.
        """
        job_id = self._place_order(
            concept_id=concept_id,
            spatial=spatial,
            temporal=temporal,
            shape=shape,
            granule_name=granule_name,
            skip_preview=skip_preview,
        )

        # Append this job to the list of job ids.
        self.job_ids.append(job_id)

        order_fn = ".order_restart"
        with open(order_fn, "w") as fid:
            # Note: icepyx v1 used "orderIds". Harmony uses the term "job" to describe
            # an order, so that gets used here.
            json.dump({"jobIds": self.job_ids}, fid)

        print("Harmony job ID: ", job_id)
        status = self.check_order_status(job_id)
        print(f"Initial status of your harmony order request: {status['status']}")
        # The list of possible statues are here:
        # https://github.com/nasa/harmony/blob/8b2eb47feab5283d237f3679ac8e09f50e85038f/db/db.sql#L8
        return job_id

    def _download_job_results(
        self,
        job_id: str,
        download_dir: Path,
        overwrite: bool,
    ) -> list[Path]:
        print(f"Downloading results for harmony job {job_id}")

        futures = self.harmony_client.download_all(
            job_id, str(download_dir), overwrite=overwrite
        )

        paths = []
        for future in as_completed(futures):
            paths.append(Path(future.result()))

        return paths

    def download_granules(
        self, download_dir: Path, overwrite: bool = False
    ) -> list[Path]:
        """
        Download all granules associated with current order.

        This method retrieves and downloads granules for all job IDs stored in
        `self.job_ids`, saving them to the specified directory.

        Parameters
        ----------
        download_dir : Path
            The directory where granules should be saved.
        overwrite : bool, optional
            Whether to overwrite existing files (default is False).

        Returns
        -------
        list of Path
            A list of file paths to the downloaded granules.
        """
        all_paths = []
        for job_id in self.job_ids:
            paths = self._download_job_results(
                job_id=job_id, download_dir=download_dir, overwrite=overwrite
            )
            all_paths.extend(paths)

        return all_paths
