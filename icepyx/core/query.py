"""Icepyx v2 work-in-progress query module.

This module is a work-in-progress and re-implements the core functionality of
`icepyx.Query` using `earthaccess` and `harmony-py` in preparation for NSIDC's
decommissioning of the ECS-based ordering system. See the
`HARMONY_MIGRATION_NOTES` for more details.

The intent is to have the `QueryV2` class replace the existing, v1 `Query`
class. Once core functionality is implemented, relevant "V2" classes/functions
can be renamed and the v1 versions removed.
"""

import json
import logging
from pathlib import Path
from pprint import pprint
import sys
import time
from typing import Any, Dict, Union

from deprecated import deprecated
import earthaccess
import harmony

import icepyx.core.APIformatting as apifmt
from icepyx.core.base_query import BaseQuery
from icepyx.core.granules import Granules, gran_IDs
from icepyx.core.harmony import HarmonyApi, HarmonyTemporal
from icepyx.core.orders import DataOrder
import icepyx.core.temporal as tp
from icepyx.core.types import CMRParams
import icepyx.core.validate_inputs as val
from icepyx.core.variables import Variables


class Query(BaseQuery):
    _temporal: Union[tp.Temporal, None]
    _CMRparams: apifmt.CMRParameters
    REQUEST_RETRY_INTERVAL_SECONDS = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensure that the `_temporal` attr is set. This simplifies checking if
        # temporal parameters has been passed. Instead of using `hasattr`, we
        # can just check for `None`.
        if not hasattr(self, "_temporal"):
            self._temporal = None  # type: ignore[reportIncompatibleVariableOverride]

        logging.basicConfig(level=logging.WARNING)

        cycles = kwargs.get("cycles")
        tracks = kwargs.get("tracks")
        if cycles or tracks:
            # get lists of available ICESat-2 cycles and tracks
            self._cycles = val.cycles(cycles)
            self._tracks = val.tracks(tracks)
            # create list of CMR parameters for granule name
            self._readable_granule_name = apifmt._fmt_readable_granules(
                self._prod, cycles=self.cycles, tracks=self.tracks
            )

    # Properties

    def __str__(self):
        str = "Product {2} v{3}\n{0}\nDate range {1}".format(
            self.spatial_extent, self.dates, self.product, self.product_version
        )
        return str

    @property
    def product(self):
        """
        Return the short name product ID string associated with the query object.

        Examples
        --------
        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> reg_a.product
        'ATL06'
        """
        return self._prod

    @property
    def product_version(self):
        """
        Return the product version of the data object.

        Examples
        --------
        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> reg_a.product_version
        '006'

        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28'], version='4')
        >>> reg_a.product_version
        '004'
        """
        return self._version

    @property
    def cycles(self):
        """
        Return the unique ICESat-2 orbital cycle.

        Examples
        --------
        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> reg_a.cycles
        ['No orbital parameters set']

        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71], cycles=['03','04'], tracks=['0849','0902'])
        >>> reg_a.cycles
        ['03', '04']
        """
        if not hasattr(self, "_cycles"):
            return ["No orbital parameters set"]
        else:
            return sorted(set(self._cycles))

    @property
    def tracks(self):
        """
        Return the unique ICESat-2 Reference Ground Tracks

        Examples
        --------
        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> reg_a.tracks
        ['No orbital parameters set']

        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71], cycles=['03','04'], tracks=['0849','0902'])
        >>> reg_a.tracks
        ['0849', '0902']
        """
        if not hasattr(self, "_tracks"):
            return ["No orbital parameters set"]
        else:
            return sorted(set(self._tracks))

    def _get_concept_id(self, product, version) -> Union[str, None]:
        collections = earthaccess.search_datasets(
            short_name=product, version=version, cloud_hosted=True
        )
        if collections:
            return collections[0].concept_id()
        else:
            return None

    @property
    @deprecated(
        version="1.4.0", reason="order_vars() is going away, use variables() instead"
    )
    def order_vars(self) -> Union[Variables, None]:
        """This used to print the list of vasriables for subsetting, Harmony doesn't provide that for IS2 datasets.
        we do need to implement a class that gets the variables even if it'sm only for listing.
        """
        logging.warning(
            "Deprecated: order_vars() is going away, use variables() instead"
        )
        if self.product:
            self._variables = Variables(product=self.product)  # type: ignore[no-any-return]
            return self._variables
        return None

    @property
    def variables(self) -> Variables:
        if not hasattr(self, "_variables"):
            self._variables = Variables(product=self.product)
        return self._variables

    def show_custom_options(self) -> Dict[str, Any]:
        """
        Display customization/subsetting options available for this product.

        """
        capabilities: dict = {}
        if not hasattr(self, "harmony_api"):
            self.harmony_api = HarmonyApi()
        if self.concept_id:
            capabilities = self.harmony_api.get_capabilities(concept_id=self.concept_id)
            print(json.dumps(capabilities, indent=2))
        return capabilities

    @property
    def CMRparams(self) -> CMRParams:
        """
        Display the CMR key:value pairs that will be submitted.
        It generates the dictionary if it does not already exist.

        Examples
        --------
        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> reg_a.CMRparams
        {'temporal': '2019-02-20T00:00:00Z,2019-02-28T23:59:59Z',
        'bounding_box': '-55.0,68.0,-48.0,71.0'}
        """

        if not hasattr(self, "_CMRparams"):
            self._CMRparams = apifmt.Parameters("CMR")

        # dictionary of optional CMR parameters
        kwargs = {}
        kwargs["concept_id"] = self._get_concept_id(self.product, None)

        # temporal CMR parameters
        if hasattr(self, "_temporal") and self.product != "ATL11" and self._temporal:
            kwargs["start"] = self._temporal._start
            kwargs["end"] = self._temporal._end
        # granule name CMR parameters (orbital or file name)
        # DevGoal: add to file name search to optional queries
        if hasattr(self, "_readable_granule_name"):
            kwargs["options[readable_granule_name][pattern]"] = "true"
            kwargs["options[spatial][or]"] = "true"
            kwargs["readable_granule_name[]"] = self._readable_granule_name

        if self._CMRparams.fmted_keys == {}:
            self._CMRparams.build_params(
                extent_type=self._spatial._ext_type,
                spatial_extent=self._spatial.fmt_for_CMR(),
                **kwargs,
            )

        return self._CMRparams.fmted_keys  # type: ignore[no-any-return]

    @property
    def granules(self):
        """
        Return the granules object, which provides the underlying functionality for searching, ordering,
        and downloading granules for the specified product.
        Users are encouraged to use the built-in wrappers
        rather than trying to access the granules object themselves.

        See Also
        --------
        avail_granules
        order_granules
        download_granules
        granules.Granules

        Examples
        --------
        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28']) # doctest: +SKIP
        >>> reg_a.granules # doctest: +SKIP
        <icepyx.core.granules.Granules at [location]>
        """

        if not hasattr(self, "_granules") or self._granules is None:
            self._granules = Granules()

        return self._granules

    # DevGoal: check to make sure the see also bits of the docstrings work properly in RTD
    def avail_granules(self, ids=False, cycles=False, tracks=False, cloud=False):
        """
        Obtain information about the available granules for the query
        object's parameters. By default, a complete list of available granules is
        obtained and stored in the object, but only summary information is returned.
        Lists of granule IDs, cycles and RGTs can be obtained using the boolean triggers.

        Parameters
        ----------
        ids : boolean, default False
            Indicates whether the function should return a list of granule IDs.

        cycles : boolean, default False
            Indicates whether the function should return a list of orbital cycles.

        tracks : boolean, default False
            Indicates whether the function should return a list of RGTs.

        cloud : boolean, default False
            Indicates whether the function should return data available in the cloud.
            Note: except in rare cases while data is in the process of being appended to,
            data available in the cloud and for download via on-premesis will be identical.

        Examples
        --------
        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> reg_a.avail_granules()
        {'Number of available granules': 4,
        'Average size of granules (MB)': np.float64(55.166646003723145),
        'Total size of all granules (MB)': 220.66658401489258}

        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-23'])
        >>> reg_a.avail_granules(ids=True)
        [['ATL06_20190221121851_08410203_006_01.h5', 'ATL06_20190222010344_08490205_006_01.h5']]
        >>> reg_a.avail_granules(cycles=True)
        [['02', '02']]
        >>> reg_a.avail_granules(tracks=True)
        [['0841', '0849']]
        """

        #         REFACTOR: add test to make sure there's a session
        if not hasattr(self, "_granules"):
            self.granules
        try:
            self.granules.avail
        except AttributeError:
            self.granules.get_avail(self.CMRparams)

        if ids or cycles or tracks or cloud:
            # list of outputs in order of ids, cycles, tracks, cloud
            return gran_IDs(
                self.granules.avail,
                ids=ids,
                cycles=cycles,
                tracks=tracks,
                cloud=cloud,
            )
        else:
            return self.granules.avail

    def _order_subset_granules(self, skip_preview: bool = False) -> str:
        concept_id = self._get_concept_id(
            product=self._prod,
            version=self._version,
        )

        if concept_id is None:
            raise ValueError(
                f"Could not find concept ID for {self._prod} v{self._version}"
            )

        readable_granule_name = self.CMRparams.get("readable_granule_name[]", [])
        harmony_temporal = None
        harmony_spatial = None
        if self._temporal:
            # TODO: this assumes there will always be a start and stop
            # temporal range. Harmony can accept start without stop and
            # vice versa.
            harmony_temporal = HarmonyTemporal(
                start=self._temporal.start,
                stop=self._temporal.end,
            )
        if self.spatial:
            if self.spatial.extent_type == "bounding_box":
                # Bounding box case.

                # TODO: think more about how this can be DRYed out. We call
                # `place_order` based on the user spatial input. The bounding box case
                # is simple, but polygons are more complicated because `harmony-py`
                # expects a shapefile (e.g,. geojson) to exist on disk.
                harmony_spatial = harmony.BBox(
                    w=self.spatial.extent[0],
                    s=self.spatial.extent[1],
                    e=self.spatial.extent[2],
                    n=self.spatial.extent[3],
                )
            elif self.spatial.extent_file or self.spatial.extent_type == "polygon":
                harmony_spatial = self.spatial.extent_as_gdf.iloc[0].geometry.wkt
                # Polygons must be passed to `harmony-py` as a path to a valid
                # shapefile (json, geojson, kml, shz, or zip). Create a temporary
                # directory to store this file for the harmony order.
            else:
                raise NotImplementedError(
                    "Only bounding box and polygon spatial subsetting is supported."
                )
        else:
            if harmony_temporal is None:
                raise ValueError("No temporal or spatial parameters provided.")

        job_id = self.harmony_api.place_order(
            concept_id=concept_id,
            temporal=harmony_temporal,
            spatial=harmony_spatial,
            granule_name=list(readable_granule_name),
            skip_preview=skip_preview,
        )
        return job_id

    def get_granule_links(self, cloud_hosted=False) -> list[str]:
        links = []
        if not hasattr(self.granules, "avail"):
            self.granules.get_avail(self.CMRparams)
        for granule in self.granules.avail:
            for link in granule["links"]:
                if (
                    cloud_hosted
                    and link["rel"] == "http://esipfed.org/ns/fedsearch/1.1/s3#"
                    or (
                        (link["rel"] == "http://esipfed.org/ns/fedsearch/1.1/data#")
                        and (
                            "type" in link
                            and link["type"]
                            in ["application/x-hdf5", "application/x-hdfeos"]
                        )
                    )
                ):
                    links.append(link["href"])
        return links

    def _order_whole_granules(self, cloud_hosted=False, path="./") -> list[str]:
        """
        Downloads the whole granules for the query object. This is not an asnc operation
        and will block until the download is complete.

        Parameters
        ----------
        cloud_hosted : bool, default False
            If True, download the cloud-hosted version of the granules. Otherwise, download
            the on-premises version. We need to run the code in the AWS cloud (us-west-2)
        path : str, default "./"
            The local directory to download the granules to.

        """

        links = self.get_granule_links(cloud_hosted=cloud_hosted)
        files = earthaccess.download(links, local_path=path)
        return files

    def skip_preview(self):
        """
        skips preview for current order
        """
        if self.last_order and self.last_order.type == "subset":
            status = self.last_order.status()
            if status["status"] == "PREVIEW":
                return self.last_order.resume()

    def order_granules(
        self, subset: bool = True, skip_preview: bool = False, path: str = "./"
    ) -> DataOrder:
        """
        Place an order for the available granules for the query object.

        Parameters
        ----------
        subset :
            Apply subsetting to the data order using harmony, returning only data that meets the
            subset parameters. Spatial and temporal subsetting based on the input parameters happens
            by default when subset=True, but additional subsetting options are available.
            Spatial subsetting returns all data that are within the area of interest (but not complete
            granules. This eliminates false-positive granules returned by the metadata-level search)
        path :
            The directory where granules should be saved, used when we order full granules.
        skip_preview : bool, default False
            If True, bypass the preview state when we order subsetting queries that exceed 300 granules.

        See Also
        --------
        harmony.place_order

        Examples
        --------
        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28']) # doctest: +SKIP
        >>> reg_a.order_granules() # doctest: +SKIP
        Harmony job ID:  931355e8-0005-4dff-9c76-7903a5be283d
        [order status output]
        Harmony provided these error messages:
        [if any were returned from the harmony subsetter, e.g. No data found that matched subset constraints.]
        Your harmony order is:  complete
        """

        # only instantiate the client when we are about to order data
        self.harmony_api = HarmonyApi()
        if subset:
            job_id = self._order_subset_granules(skip_preview=skip_preview)
            self.last_order = DataOrder(
                job_id, "subset", self.granules, self.harmony_api
            )
            return self.last_order
        else:
            files = self._order_whole_granules(path=path)
            self.last_order = DataOrder(None, "whole", files, self.harmony_api)
            return self.last_order

    def download_granules(
        self,
        path: Path,
        overwrite: bool = False,
    ) -> Union[list[str], None]:
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
            A list of the downloaded file paths if successful, otherwise None.
        """
        # Order granules based on user selections if restart is False and there
        # are no job IDs registered by the harmony API
        if hasattr(self, "last_order") is None:
            raise ValueError("No order has been placed yet.")
        status = self.last_order.status()
        if status["status"] == "running" or status["status"] == "accepted":
            print(
                (
                    "Your harmony job status is still "
                    f"{status['status']}. Please continue waiting... this may take a few moments."
                )
            )
            while (
                status["status"].startswith("running") or status["status"] == "accepted"
            ):
                sys.stdout.write(".")
                sys.stdout.flush()
                # Requesting the status too often can result in a 500 error.
                time.sleep(self.REQUEST_RETRY_INTERVAL_SECONDS)
                status = self.last_order.status()

        if status["status"] == "complete_with_errors" or status["status"] == "failed":
            print("Harmony provided these error messages:")
            pprint(status["errors"])
            return None
        else:
            return self.last_order.download(path, overwrite=overwrite)
