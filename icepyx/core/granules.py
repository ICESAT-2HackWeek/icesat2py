from __future__ import annotations

import datetime
import io
import json
import os
import pprint
import re
import time
from xml.etree import ElementTree as ET
import zipfile

import numpy as np
import requests
from requests.compat import unquote

import icepyx.core.APIformatting as apifmt
from icepyx.core.auth import EarthdataAuthMixin
import icepyx.core.exceptions
from icepyx.core.types import (
    CMRParams,
    EGIRequiredParamsDownload,
)
from icepyx.core.urls import DOWNLOAD_BASE_URL, GRANULE_SEARCH_BASE_URL, ORDER_BASE_URL


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

    # DevNote: currently, default subsetting DOES NOT include variable subsetting,
    # only spatial and temporal
    # DevGoal: add kwargs to allow subsetting and more control over request options.
    def place_order(
        self,
        CMRparams: CMRParams,
        reqparams: EGIRequiredParamsDownload,
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
        reqparams :
            Dictionary of properly formatted parameters required for searching, ordering,
            or downloading from NSIDC (via their EGI system).
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

        self.get_avail(CMRparams)

        if subset is False:
            request_params = apifmt.combine_params(
                CMRparams, reqparams, {"agent": "NO"}
            )
        else:
            request_params = apifmt.combine_params(CMRparams, reqparams, subsetparams)

        order_fn = ".order_restart"

        total_pages = int(np.ceil(len(self.avail) / reqparams["page_size"]))
        print(
            "Total number of data order requests is ",
            total_pages,
            " for ",
            len(self.avail),
            " granules.",
        )

        if reqparams["page_num"] > 0:
            pagenums = [reqparams["page_num"]]
        else:
            pagenums = range(1, total_pages + 1)

        for page_num in pagenums:
            print(
                "Data request ",
                page_num,
                " of ",
                total_pages,
                " is submitting to NSIDC",
            )
            request_params.update({"page_num": page_num})

            request = self.session.get(ORDER_BASE_URL, params=request_params)

            # DevGoal: use the request response/number to do some error handling/
            # give the user better messaging for failures
            # print(request.content)
            # root = ET.fromstring(request.content)
            # print([subset_agent.attrib for subset_agent in root.iter('SubsetAgent')])

            if verbose is True:
                print("Request HTTP response: ", request.status_code)
                # print('Order request URL: ', request.url)

            # Raise bad request: Loop will stop for bad response code.
            request.raise_for_status()
            esir_root = ET.fromstring(request.content)
            if verbose is True:
                print("Order request URL: ", unquote(request.url))
                print(
                    "Order request response XML content: ",
                    request.content.decode("utf-8"),
                )

            # Look up order ID
            orderlist = []
            for order in esir_root.findall("./order/"):
                # if verbose is True:
                #     print(order)
                orderlist.append(order.text)
            orderID = orderlist[0]
            print("order ID: ", orderID)

            # Create status URL
            statusURL = f"{ORDER_BASE_URL}/{orderID}"
            if verbose is True:
                print("status URL: ", statusURL)

            # Find order status
            request_response = self.session.get(statusURL)
            if verbose is True:
                print(
                    "HTTP response from order response URL: ",
                    request_response.status_code,
                )

            # Raise bad request: Loop will stop for bad response code.
            request_response.raise_for_status()
            request_root = ET.fromstring(request_response.content)
            statuslist = []
            for status in request_root.findall("./requestStatus/"):
                statuslist.append(status.text)
            status = statuslist[0]
            print("Initial status of your order request at NSIDC is: ", status)

            loop_root = None
            # If status is already finished without going into pending/processing
            if status.startswith("complete"):
                loop_response = self.session.get(statusURL)
                loop_root = ET.fromstring(loop_response.content)

            # Continue loop while request is still processing
            while status == "pending" or status == "processing":
                print(
                    "Your order status is still ",
                    status,
                    " at NSIDC. Please continue waiting... this may take a few moments.",
                )
                # print('Status is not complete. Trying again')
                time.sleep(10)
                loop_response = self.session.get(statusURL)

                # Raise bad request: Loop will stop for bad response code.
                loop_response.raise_for_status()
                loop_root = ET.fromstring(loop_response.content)

                # find status
                statuslist = []
                for status in loop_root.findall("./requestStatus/"):
                    statuslist.append(status.text)
                status = statuslist[0]
                # print('Retry request status is: ', status)
                if status == "pending" or status == "processing":
                    continue

            if not isinstance(loop_root, ET.Element):
                # The typechecker needs help knowing that at this point loop_root is
                # set, as it can't tell that the conditionals above are supposed to be
                # exhaustive.
                raise icepyx.core.exceptions.ExhaustiveTypeGuardException

            # Order can either complete, complete_with_errors, or fail:
            # Provide complete_with_errors error message:
            if status == "complete_with_errors" or status == "failed":
                messagelist = []
                for message in loop_root.findall("./processInfo/"):
                    messagelist.append(message.text)
                print("Your order is: ", status)
                print("NSIDC provided these error messages:")
                pprint.pprint(messagelist)

            if status == "complete" or status == "complete_with_errors":
                print("Your order is:", status)
                messagelist = []
                for message in loop_root.findall("./processInfo/info"):
                    messagelist.append(message.text)
                if messagelist != []:
                    print("NSIDC returned these messages")
                    pprint.pprint(messagelist)
                if not hasattr(self, "orderIDs"):
                    self.orderIDs = []

                self.orderIDs.append(orderID)
            else:
                print("Request failed.")

            # DevGoal: save orderIDs more frequently than just at the end for large orders
            # (e.g. for len(reqparams['page_num']) > 5 or 10 or something)
            # Save orderIDs to file to avoid resubmitting order in case kernel breaks down.
            # save orderIDs for every 5 orders when more than 10 orders are submitted.
            if reqparams["page_num"] >= 10:
                with open(order_fn, "w") as fid:
                    json.dump({"orderIDs": self.orderIDs}, fid)

        # --- Output the final orderIDs
        with open(order_fn, "w") as fid:
            json.dump({"orderIDs": self.orderIDs}, fid)

        return self.orderIDs

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
        order_fn = ".order_restart"
        if os.path.exists(order_fn):
            with open(order_fn, "r") as fid:
                order_dat = json.load(fid)
                self.orderIDs = order_dat["orderIDs"]

        if not hasattr(self, "orderIDs") or len(self.orderIDs) == 0:
            raise ValueError(
                "Please confirm that you have submitted a valid order and it has successfully completed."
            )

        # DevNote: Temporary. Hard code the orderID info files here.
        # order_fn should be consistent with place_order.

        downid_fn = ".download_ID"

        i_order = 0

        if restart:
            print("Restarting download ... ")

            # --- update the starting point of download list
            if os.path.exists(downid_fn):
                order_start = str(int(np.loadtxt(downid_fn)))
                i_order = self.orderIDs.index(order_start) + 1

        for order in self.orderIDs[i_order:]:
            downloadURL = f"{DOWNLOAD_BASE_URL}/{order}.zip"
            # DevGoal: get the download_url from the granules

            if verbose is True:
                print("Zip download URL: ", downloadURL)
            print("Beginning download of zipped output...")

            try:
                zip_response = self.session.get(downloadURL)
                # Raise bad request: Loop will stop for bad response code.
                zip_response.raise_for_status()
                print(
                    "Data request",
                    order,
                    "of ",
                    len(self.orderIDs[i_order:]),
                    " order(s) is downloaded.",
                )
            except requests.HTTPError:
                print(
                    "Unable to download ", order, ". Check granule order for messages."
                )
            # DevGoal: move this option back out to the is2class level
            # and implement it in an alternate way?
            #         #Note: extract the data to save it locally
            else:
                with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
                    for zfile in z.filelist:
                        # Remove the subfolder name from the filepath
                        zfile.filename = os.path.basename(zfile.filename)
                        z.extract(member=zfile, path=path)

            # update the current finished order id and save to file
            with open(downid_fn, "w") as fid:
                fid.write(order)

        # remove orderID and download id files at the end
        if os.path.exists(order_fn):
            os.remove(order_fn)
        if os.path.exists(downid_fn):
            os.remove(downid_fn)

        print("Download complete")
