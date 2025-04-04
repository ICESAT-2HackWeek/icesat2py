from __future__ import annotations

import datetime
import json
import logging
import re

from deprecated import deprecated
import numpy as np
import requests

import icepyx.core.APIformatting as apifmt
from icepyx.core.auth import EarthdataAuthMixin
import icepyx.core.exceptions
from icepyx.core.types import CMRParams
from icepyx.core.urls import GRANULE_SEARCH_BASE_URL


def info(grans):
    """
    Return some basic summary information about a set of granules for an
    query object. Granule info may be from a list of those available
    from NSIDC (for ordering/download) or a list of granules present on the
    file system.
    """
    assert len(grans) > 0, "Your data object has no granules associated with it"
    gran_info = {}
    gran_info.update({"Number of available granules": len(grans)})

    gran_sizes = [float(gran["granule_size"]) for gran in grans]
    gran_info.update({"Average size of granules (MB)": np.mean(gran_sizes)})
    gran_info.update({"Total size of all granules (MB)": sum(gran_sizes)})

    return gran_info


# DevNote: currently this fn is not tested
# DevNote: could add flag to separate ascending and descending orbits based on ATL03 granule region
def gran_IDs(grans, ids=False, cycles=False, tracks=False, dates=False, cloud=False):
    """
    Returns a list of granule information for each granule dictionary
    in the input list of granule dictionaries.
    Granule info may be from a list of those available from NSIDC (for ordering/download)
    or a list of granules present on the file system.

    Parameters
    ----------
    grans : list of dictionaries
        List of input granule json dictionaries. Must have key "producer_granule_id"
    ids: boolean, default True
        Return a list of the available granule IDs for the granule dictionary
    cycles : boolean, default False
        Return a list of the available orbital cycles for the granule dictionary
    tracks : boolean, default False
        Return a list of the available Reference Ground Tracks (RGTs) for the granule dictionary
    dates : boolean, default False
        Return a list of the available dates for the granule dictionary.
    cloud : boolean, default False
        Return a a list of AWS s3 urls for the available granules in the granule dictionary.
    """
    assert len(grans) > 0, "Your data object has no granules associated with it"
    # regular expression for extracting parameters from file names
    rx = re.compile(
        r"(ATL\d{2})(-\d{2})?_(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})"
        r"(\d{2})_(\d{4})(\d{2})(\d{2})_(\d{3})_(\d{2})(.*?).(.*?)$"
    )
    gran_ids = []
    gran_cycles = []
    gran_tracks = []
    gran_dates = []
    gran_s3urls = []
    for gran in grans:
        producer_granule_id = gran["producer_granule_id"]
        gran_ids.append(producer_granule_id)

        if cloud is True:
            try:
                for link in gran["links"]:
                    href = link["href"]
                    if href.startswith("s3") and href.endswith((".h5", "nc")):
                        gran_s3urls.append(href)
            except KeyError:
                pass

        if any(param is True for param in [cycles, tracks, dates]):
            # PRD: ICESat-2 product
            # HEM: Sea Ice Hemisphere flag
            # YY,MM,DD,HH,MN,SS: Year, Month, Day, Hour, Minute, Second
            # TRK: Reference Ground Track (RGT)
            # CYCL: Orbital Cycle
            # GRAN: Granule region (1-14)
            # RL: Data Release
            # VERS: Product Version
            # AUX: Auxiliary flags
            # SFX: Suffix (h5)
            (
                PRD,
                HEM,
                YY,
                MM,
                DD,
                HH,
                MN,
                SS,
                TRK,
                CYCL,
                GRAN,
                RL,
                VERS,
                AUX,
                SFX,
            ) = rx.findall(producer_granule_id).pop()
            gran_cycles.append(CYCL)
            gran_tracks.append(TRK)
            gran_dates.append(
                str(datetime.datetime(year=int(YY), month=int(MM), day=int(DD)).date())
            )

    # list of granule parameters
    gran_list = []
    # granule IDs
    if ids:
        gran_list.append(gran_ids)
    # orbital cycles
    if cycles:
        gran_list.append(gran_cycles)
    # reference ground tracks (RGTs)
    if tracks:
        gran_list.append(gran_tracks)
    # granule date
    if dates:
        gran_list.append(gran_dates)
    # AWS s3 url
    if cloud:
        gran_list.append(gran_s3urls)
    # return the list of granule parameters
    return gran_list


# DevGoal: this will be a great way/place to manage data from the local file system
# where the user already has downloaded data!
# DevNote: currently this class is not tested
class Granules(EarthdataAuthMixin):
    """
    Interact with ICESat-2 data granules. This includes finding,
    ordering, and downloading them as well as (not yet implemented) getting already
    downloaded granules into the query object.

    Returns
    -------
    Granules object
    """

    def __init__(
        self,
        # avail=[],
        # orderIDs=[],
        # files=[],
        # session=None
    ):
        # initialize authentication properties
        EarthdataAuthMixin.__init__(self)

        # self.avail = avail
        # self.orderIDs = orderIDs
        # self.files = files
        # session = session

    # ----------------------------------------------------------------------
    # Methods

    def get_avail(
        self,
        CMRparams: CMRParams,
        cloud: bool = False,
    ):
        """
        Get a list of available granules for the query object's parameters.
        Generates the `avail` attribute of the granules object.

        Parameters
        ----------
        CMRparams :
            Dictionary of properly formatted CMR search parameters.
        cloud :
            CMR metadata is always collected for the cloud system.

            .. deprecated:: 1.2
                This parameter is ignored.

        Notes
        -----
        This function is used by ``query.Query.avail_granules()``, which automatically
        feeds in the required parameters.

        See Also
        --------
        APIformatting.Parameters
        query.Query.avail_granules
        """

        assert CMRparams is not None, "Missing required input parameter dictionaries"

        # if not hasattr(self, 'avail'):
        self.avail = []

        headers = {"Accept": "application/json", "Client-Id": "icepyx"}
        # note we should also check for errors whenever we ping NSIDC-API -
        # make a function to check for errors

        params = CMRparams

        cmr_search_after = None

        while True:
            if cmr_search_after is not None:
                headers["CMR-Search-After"] = cmr_search_after

            response = requests.get(
                GRANULE_SEARCH_BASE_URL,
                headers=headers,
                params=apifmt.to_string(params),
            )

            try:
                cmr_search_after = response.headers["CMR-Search-After"]
            except KeyError:
                cmr_search_after = None

            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                if (
                    b"errors" in response.content
                ):  # If CMR returns a bad status with extra information, display that
                    raise icepyx.core.exceptions.NsidcQueryError(
                        response.json()["errors"]
                    )  # exception chaining will display original exception too
                else:  # If no 'errors' key, just reraise original exception
                    raise e

            results = json.loads(response.content)
            if not results["feed"]["entry"]:
                assert len(self.avail) == int(response.headers["CMR-Hits"]), (
                    "Search failure - unexpected number of results"
                )
                break

            # Collect results
            self.avail.extend(results["feed"]["entry"])

        assert len(self.avail) > 0, (
            "Your search returned no results; try different search parameters"
        )

    @deprecated("Use `Query.place_order` instead.")
    def place_order(
        self,
        CMRparams: CMRParams,
        subsetparams,
        verbose,
        subset=True,
        geom_filepath=None,
    ):
        """
        Place an order for the available granules for the query object.
        Adds the list of zipped files (orders) to the granules data object (which is
        stored as the `granules` attribute of the query object).
        You must be logged in to Earthdata to use this function.

        Parameters
        ----------
        CMRparams :
            Dictionary of properly formatted CMR search parameters.
        subsetparams : dictionary
            Dictionary of properly formatted subsetting parameters. An empty dictionary
            is passed as input here when subsetting is set to False in query methods.
        verbose : boolean, default False
            Print out all feedback available from the order process.
            Progress information is automatically printed regardless of the value of verbose.
        subset : boolean, default True
            Apply subsetting to the data order from the NSIDC, returning only data that meets the
            subset parameters.
            Spatial and temporal subsetting based on the input parameters happens
            by default when subset=True, but additional subsetting options are available.
            Spatial subsetting returns all data that are within the area of interest
            (but not complete granules.
            This eliminates false-positive granules returned by the metadata-level search)
        geom_filepath : string, default None
            String of the full filename and path when the spatial input is a file.

        Notes
        -----
        This function is used by query.Query.order_granules(), which automatically
        feeds in the required parameters.

        See Also
        --------
        query.Query.order_granules
        """
        logging.warning("Deprecated:  Use Query.place_order instead")

        return DeprecationWarning(
            "This function is deprecated. Use `Query.place_order` instead."
        )

    @deprecated("Use `Query.download_granules` instead.")
    def download(self, verbose, path, restart=False):
        """
        Downloads the data for the object's orderIDs, which are generated by ordering data
        from the NSIDC.

        Parameters
        ----------
        verbose : boolean, default False
            Print out all feedback available from the order process.
            Progress information is automatically printed regardless of the value of verbose.
        path : string
            String with complete path to desired download directory and location.
        restart : boolean, default False
            Restart your download if it has been interrupted.
            If the kernel has been restarted, but you successfully
            completed your order, you will need to re-initialize your query class object
            and can then skip immediately to the download_granules method with restart=True.

        Notes
        -----
        This function is used by query.Query.download_granules(), which automatically
        feeds in the required parameters.

        See Also
        --------
        query.Query.download_granules
        """

        # DevNote: this will replace any existing orderIDs with the saved list
        # (could create confusion depending on whether download was interrupted or kernel restarted)
        logging.warning("Deprecated:  Use Query.download_granules instead")
        return DeprecationWarning(
            "This function is deprecated. Use `Query.download_granules` instead."
        )
