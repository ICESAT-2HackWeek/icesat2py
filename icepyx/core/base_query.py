from functools import cached_property
import pprint
from typing import Union

import earthaccess
import geopandas as gpd
import matplotlib.pyplot as plt

from icepyx.core.auth import EarthdataAuthMixin
import icepyx.core.is2ref as is2ref
import icepyx.core.spatial as spat
import icepyx.core.temporal as tp
import icepyx.core.validate_inputs as val
from icepyx.core.variables import Variables as Variables
from icepyx.core.visualization import Visualize


class GenQuery:
    """
    Base class for querying data.

    Generic components of query object that specifically handles
    spatio-temporal constraints applicable to all datasets.
    Extended by Query (ICESat-2) and Quest (other products).

    Parameters
    ----------
    spatial_extent : list of coordinates or string (i.e. file name)
        Spatial extent of interest, provided as a bounding box,
        list of polygon coordinates, or
        geospatial polygon file.
        NOTE: Longitude values are assumed to be in the range -180 to +180,
        with 0 being the Prime Meridian (Greenwich).
        See xdateline for regions crossing the date line.
        You can submit at most one bounding box or list of polygon coordinates.
        Per NSIDC requirements, geospatial polygon files may only contain one feature (polygon).
        Bounding box coordinates should be provided in decimal degrees as
        [lower-left-longitude, lower-left-latitute,
        upper-right-longitude, upper-right-latitude].
        Polygon coordinates should be provided as coordinate pairs in decimal degrees as
        [(longitude1, latitude1), (longitude2, latitude2), ... (longitude_n,latitude_n), (longitude1,latitude1)]
        or
        [longitude1, latitude1, longitude2, latitude2, ... longitude_n,latitude_n, longitude1,latitude1].
        Your list must contain at least four points, where the first and last are identical.
        Geospatial polygon files are entered as strings with the full file path and
        must contain only one polygon with the area of interest.
        Currently supported formats are: kml, shp, and gpkg
    date_range : list or dict, as follows
        Date range of interest, provided as start and end dates, inclusive.
        Accepted input date formats are:
            * YYYY-MM-DD string
            * YYYY-DOY string
            * datetime.date object (if times are included)
            * datetime.datetime objects (if no times are included)
        where YYYY = 4 digit year, MM = 2 digit month, DD = 2 digit day, DOY = 3 digit day of year.
        Date inputs are accepted as a list or dictionary with `start_date` and `end_date` keys.
        Currently, a list of specific dates (rather than a range) is not accepted.
        TODO: allow searches with a list of dates, rather than a range.
    start_time : str, datetime.time, default None
        Start time in UTC/Zulu (24 hour clock).
        Input types are  an HH:mm:ss string or datetime.time object
        where HH = hours, mm = minutes, ss = seconds.
        If None is given (and a datetime.datetime object is not supplied for `date_range`),
        a default of 00:00:00 is applied.
    end_time : str, datetime.time, default None
        End time in UTC/Zulu (24 hour clock).
        Input types are  an HH:mm:ss string or datetime.time object
        where HH = hours, mm = minutes, ss = seconds.
        If None is given (and a datetime.datetime object is not supplied for `date_range`),
        a default of 23:59:59 is applied.
        If a datetime.datetime object was created without times,
        the datetime package defaults will apply over those of icepyx
    xdateline : boolean, default None
        Keyword argument to enforce spatial inputs that cross the International Date Line.
        Internally, this will translate your longitudes to 0 to 360 to construct the
        correct, valid Shapely geometry.

        WARNING: This will allow your request to be properly submitted and visualized.
        However, this flag WILL NOT automatically correct for incorrectly ordered spatial inputs.

    Examples
    --------
    Initializing Query with a bounding box

    >>> reg_a_bbox = [-55, 68, -48, 71]
    >>> reg_a_dates = ['2019-02-20','2019-02-28']
    >>> reg_a = GenQuery(reg_a_bbox, reg_a_dates)
    >>> print(reg_a)
    Extent type: bounding_box
    Coordinates: [-55.0, 68.0, -48.0, 71.0]
    Date range: (2019-02-20 00:00:00, 2019-02-28 23:59:59)

    Initializing Query with a list of polygon vertex coordinate pairs.

    >>> reg_a_poly = [(-55, 68), (-55, 71), (-48, 71), (-48, 68), (-55, 68)]
    >>> reg_a_dates = ['2019-02-20','2019-02-28']
    >>> reg_a = GenQuery(reg_a_poly, reg_a_dates)
    >>> print(reg_a)
    Extent type: polygon
    Coordinates: [-55.0, 68.0, -55.0, 71.0, -48.0, 71.0, -48.0, 68.0, -55.0, 68.0]
    Date range: (2019-02-20 00:00:00, 2019-02-28 23:59:59)

    Initializing Query with a geospatial polygon file.

    >>> from pathlib import Path
    >>> aoi = Path('./doc/source/example_notebooks/supporting_files/simple_test_poly.gpkg').resolve()
    >>> reg_a_dates = ['2019-02-22','2019-02-28']
    >>> reg_a = GenQuery(str(aoi), reg_a_dates)
    >>> print(reg_a)
    Extent type: polygon
    Coordinates: [-55.0, 68.0, -55.0, 71.0, -48.0, 71.0, -48.0, 68.0, -55.0, 68.0]
    Date range: (2019-02-22 00:00:00, 2019-02-28 23:59:59)

    See Also
    --------
    Query
    Quest
    """

    _temporal: tp.Temporal

    def __init__(
        self,
        spatial_extent=None,
        date_range=None,
        start_time=None,
        end_time=None,
        **kwargs,
    ):
        # validate & init spatial extent
        if "xdateline" in kwargs:
            self._spatial = spat.Spatial(spatial_extent, xdateline=kwargs["xdateline"])
        else:
            self._spatial = spat.Spatial(spatial_extent)

        # valiidate and init temporal constraints
        if date_range:
            self._temporal = tp.Temporal(date_range, start_time, end_time)

    def __str__(self):
        str = "Extent type: {0} \nCoordinates: {1}\nDate range: ({2}, {3})".format(
            self._spatial._ext_type,
            self._spatial._spatial_ext,
            self._temporal._start,
            self._temporal._end,
        )
        return str

    # ----------------------------------------------------------------------
    # Properties

    @property
    def temporal(self) -> Union[tp.Temporal, list[str]]:
        """
        Return the Temporal object containing date/time range information for the query object.

        See Also
        --------
        temporal.Temporal.start
        temporal.Temporal.end
        temporal.Temporal

        Examples
        --------
        >>> reg_a = GenQuery([-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> print(reg_a.temporal)
        Start date and time: 2019-02-20 00:00:00
        End date and time: 2019-02-28 23:59:59

        >>> reg_a = GenQuery([-55, 68, -48, 71],cycles=['03','04','05','06','07'], tracks=['0849','0902'])
        >>> print(reg_a.temporal)
        ['No temporal parameters set']
        """

        if hasattr(self, "_temporal") and self._temporal is not None:
            return self._temporal
        else:
            return ["No temporal parameters set"]

    @property
    def spatial(self):
        """
        Return the spatial object, which provides the underlying functionality for validating
        and formatting geospatial objects. The spatial object has several properties to enable
        user access to the stored spatial extent in multiple formats.

        See Also
        --------
        spatial.Spatial.spatial_extent
        spatial.Spatial.extent_type
        spatial.Spatial.extent_file
        spatial.Spatial

        Examples
        --------
        >>> reg_a = ipx.GenQuery([-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> reg_a.spatial # doctest: +SKIP
        <icepyx.core.spatial.Spatial at [location]>

        >>> print(reg_a.spatial)
        Extent type: bounding_box
        Coordinates: [-55.0, 68.0, -48.0, 71.0]

        """
        return self._spatial

    @property
    def spatial_extent(self):
        """
        Return an array showing the spatial extent of the query object.
        Spatial extent is returned as an input type (which depends on how
        you initially entered your spatial data) followed by the geometry data.
        Bounding box data is [lower-left-longitude, lower-left-latitute,
                            ... upper-right-longitude, upper-right-latitude].
        Polygon data is [longitude1, latitude1, longitude2, latitude2,
                        ... longitude_n,latitude_n, longitude1,latitude1].

        Returns
        -------
        tuple of length 2
        First tuple element is the spatial type ("bounding box" or "polygon").
        Second tuple element is the spatial extent as a list of coordinates.

        Examples
        --------

        # Note: coordinates returned as float, not int
        >>> reg_a = GenQuery([-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> reg_a.spatial_extent
        ('bounding_box', [-55.0, 68.0, -48.0, 71.0])

        >>> reg_a = GenQuery([(-55, 68), (-55, 71), (-48, 71), (-48, 68), (-55, 68)],['2019-02-20','2019-02-28'])
        >>> reg_a.spatial_extent
        ('polygon', [-55.0, 68.0, -55.0, 71.0, -48.0, 71.0, -48.0, 68.0, -55.0, 68.0])

        # NOTE Is this where we wanted to put the file-based test/example?
        # The test file path is: examples/supporting_files/simple_test_poly.gpkg

        See Also
        --------
        Spatial.extent
        Spatial.extent_type
        Spatial.extent_as_gdf

        """

        return (self._spatial._ext_type, self._spatial._spatial_ext)

    @property
    def dates(self) -> list[str]:
        """
        Return an array showing the date range of the query object.
        Dates are returned as an array containing the start and end datetime
        objects, inclusive, in that order.

        Examples
        --------
        >>> reg_a = ipx.GenQuery([-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> reg_a.dates
        ['2019-02-20', '2019-02-28']

        >>> reg_a = GenQuery([-55, 68, -48, 71])
        >>> reg_a.dates
        ['No temporal parameters set']
        """
        if not hasattr(self, "_temporal") or self._temporal is None:
            return ["No temporal parameters set"]
        else:
            return [
                self._temporal._start.strftime("%Y-%m-%d"),
                self._temporal._end.strftime("%Y-%m-%d"),
            ]  # could also use self._start.date()

    @property
    def start_time(self) -> Union[list[str], str]:
        """
        Return the start time specified for the start date.

        Examples
        --------
        >>> reg_a = ipx.GenQuery([-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> reg_a.start_time
        '00:00:00'

        >>> reg_a = ipx.GenQuery([-55, 68, -48, 71],['2019-02-20','2019-02-28'], start_time='12:30:30')
        >>> reg_a.start_time
        '12:30:30'

        >>> reg_a = GenQuery([-55, 68, -48, 71])
        >>> reg_a.start_time
        ['No temporal parameters set']
        """
        if not hasattr(self, "_temporal") or self._temporal is None:
            return ["No temporal parameters set"]
        else:
            return self._temporal._start.strftime("%H:%M:%S")

    @property
    def end_time(self) -> Union[list[str], str]:
        """
        Return the end time specified for the end date.

        Examples
        --------
        >>> reg_a = ipx.GenQuery([-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> reg_a.end_time
        '23:59:59'

        >>> reg_a = ipx.GenQuery([-55, 68, -48, 71],['2019-02-20','2019-02-28'], end_time='10:20:20')
        >>> reg_a.end_time
        '10:20:20'

        >>> reg_a = GenQuery([-55, 68, -48, 71])
        >>> reg_a.end_time
        ['No temporal parameters set']
        """
        if not hasattr(self, "_temporal") or self._temporal is None:
            return ["No temporal parameters set"]
        else:
            return self._temporal._end.strftime("%H:%M:%S")


class BaseQuery(GenQuery, EarthdataAuthMixin):
    """
    Query and get ICESat-2 data

    ICESat-2 Data object to query, obtain, and perform basic operations on
    available ICESat-2 data products using temporal and spatial input parameters.
    Allows the easy input and formatting of search parameters to match the
    NASA NSIDC DAAC and (development goal-not yet implemented) conversion to multiple data types.
    Expands the superclass GenQuery.

    See the doc page for GenQuery for details on temporal and spatial input parameters.

    Parameters
    ----------
    product : string
        ICESat-2 data product ID, also known as "short name" (e.g. ATL03).
        Available data products can be found at: https://nsidc.org/data/icesat-2/data-sets
    version : string, default most recent version
        Product version, given as a 3 digit string.
        If no version is given, the current version is used. Example: "006"
    cycles : string or a list of strings, default all available orbital cycles
        Product cycle, given as a 2 digit string.
        If no cycle is given, all available cycles are used. Example: "04"
    tracks : string or a list of strings, default all available reference ground tracks (RGTs)
        Product track, given as a 4 digit string.
        If no track is given, all available reference ground tracks are used.
        Example: "0594"
    auth : earthaccess.auth.Auth, default None
        An earthaccess authentication object. Available as an argument so an existing
        earthaccess.auth.Auth object can be used for authentication. If not given, a new auth
        object will be created whenever authentication is needed.

    Returns
    -------
    query object

    Examples
    --------
    Initializing Query with a bounding box.

    >>> reg_a_bbox = [-55, 68, -48, 71]
    >>> reg_a_dates = ['2019-02-20','2019-02-28']
    >>> reg_a = Query('ATL06', reg_a_bbox, reg_a_dates)
    >>> print(reg_a)
    Product ATL06 v006
    ('bounding_box', [-55.0, 68.0, -48.0, 71.0])
    Date range ['2019-02-20', '2019-02-28']

    Initializing Query with a list of polygon vertex coordinate pairs.

    >>> reg_a_poly = [(-55, 68), (-55, 71), (-48, 71), (-48, 68), (-55, 68)]
    >>> reg_a_dates = ['2019-02-20','2019-02-28']
    >>> reg_a = Query('ATL06', reg_a_poly, reg_a_dates)
    >>> reg_a.spatial_extent
    ('polygon', [-55.0, 68.0, -55.0, 71.0, -48.0, 71.0, -48.0, 68.0, -55.0, 68.0])

    Initializing Query with a geospatial polygon file.

    >>> from pathlib import Path
    >>> aoi = Path('./doc/source/example_notebooks/supporting_files/simple_test_poly.gpkg').resolve()
    >>> reg_a_dates = ['2019-02-22','2019-02-28']
    >>> reg_a = Query('ATL06', str(aoi), reg_a_dates)
    >>> print(reg_a)
    Product ATL06 v006
    ('polygon', [-55.0, 68.0, -55.0, 71.0, -48.0, 71.0, -48.0, 68.0, -55.0, 68.0])
    Date range ['2019-02-22', '2019-02-28']

    See Also
    --------
    GenQuery
    """

    # ----------------------------------------------------------------------
    # Constructors

    def __init__(
        self,
        product=None,
        spatial_extent=None,
        date_range=None,
        start_time=None,
        end_time=None,
        version=None,
        cycles=None,
        tracks=None,
        auth=None,
        **kwargs,
    ):
        self._prod = is2ref._validate_product(product)

        super().__init__(spatial_extent, date_range, start_time, end_time, **kwargs)

        self._version = val.prod_version(is2ref.latest_version(self._prod), version)

        # initialize authentication properties
        EarthdataAuthMixin.__init__(self)

    # ----------------------------------------------------------------------
    # Properties

    def __str__(self):
        str = "Product {2} v{3}\n{0}\nDate range {1}".format(
            self.spatial_extent, self.dates, self.product, self.product_version
        )
        return str

    @cached_property
    def concept_id(self) -> Union[str, None]:
        if hasattr(self, "product"):
            short_name = self.product
        else:
            raise ValueError("Product not defined")
        if hasattr(self, "_version"):
            version = self._version
        else:
            version = is2ref.latest_version(short_name)
        collections = earthaccess.search_datasets(
            short_name=short_name, version=version, cloud_hosted=True
        )
        if collections:
            return collections[0].concept_id()
        else:
            return None

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

    # ----------------------------------------------------------------------
    # Methods - Get and display neatly information at the product level

    def product_summary_info(self):
        """
        Display a summary of selected metadata for the specified version of the product
        of interest (the collection).

        Examples
        --------
        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28'], version='006')
        >>> reg_a.product_summary_info()
        title :  ATLAS/ICESat-2 L3A Land Ice Height V006
        short_name :  ATL06
        version_id :  006
        time_start :  2018-10-14T00:00:00.000Z
        coordinate_system :  CARTESIAN
        summary :  This data set (ATL06) provides geolocated, land-ice surface heights (above the WGS 84 ellipsoid, ITRF2014 reference frame), plus ancillary parameters that can be used to interpret and assess the quality of the height estimates. The data were acquired by the Advanced Topographic Laser Altimeter System (ATLAS) instrument on board the Ice, Cloud and land Elevation Satellite-2 (ICESat-2) observatory.
        orbit_parameters :  {}
        """
        if not hasattr(self, "_about_product"):
            self._about_product = is2ref.about_product(self._prod)
        summ_keys = [
            "title",
            "short_name",
            "version_id",
            "time_start",
            "coordinate_system",
            "summary",
            "orbit_parameters",
        ]
        for key in summ_keys:
            print(key, ": ", self._about_product["feed"]["entry"][-1][key])

    def product_all_info(self):
        """
        Display all metadata about the product of interest (the collection).

        Examples
        --------
        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28']) # doctest: +SKIP
        >>> reg_a.product_all_info() # doctest: +SKIP
        {very long prettily-formatted dictionary output}

        """
        if not hasattr(self, "_about_product"):
            self._about_product = is2ref.about_product(self._prod)
        pprint.pprint(self._about_product)

    def latest_version(self):
        """
        A reference function to is2ref.latest_version.

        Determine the most recent version available for the given product.

        Examples
        --------
        >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28'])
        >>> reg_a.latest_version()
        '006'
        """
        return is2ref.latest_version(self.product)

    # DevGoal: add testing? What do we test, and how, given this is a visualization.
    # DevGoal(long term): modify this to accept additional inputs, etc.
    # DevGoal: move this to it's own module for visualizing, etc.
    # DevGoal: see Amy's data access notebook for a zoomed in map - implement here?
    def visualize_spatial_extent(
        self,
    ):  # additional args, basemap, zoom level, cmap, export
        """
        Creates a map displaying the input spatial extent

        Examples
        --------
        >>> reg_a = ipx.Query('ATL06','path/spatialfile.shp',['2019-02-22','2019-02-28']) # doctest: +SKIP
        >>> reg_a.visualize_spatial_extent # doctest: +SKIP
        [visual map output]
        """

        gdf = self._spatial.extent_as_gdf

        try:
            import geoviews as gv  # type: ignore[import]
            from shapely.geometry import Polygon  # noqa: F401

            gv.extension("bokeh")  # pyright: ignore[reportCallIssue]

            bbox_poly = gv.Path(gdf["geometry"]).opts(color="red", line_color="red")
            tile = gv.tile_sources.EsriImagery.opts(width=500, height=500)
            return tile * bbox_poly  # pyright: ignore[reportOperatorIssue]

        except ImportError:
            legacy_url = "https://github.com/geopandas/geopandas/raw/refs/heads/0.8.x/geopandas/datasets/naturalearth_lowres/naturalearth_lowres.shp"
            world = gpd.read_file(legacy_url)  # pyright: ignore[reportAttributeAccessIssue]
            f, ax = plt.subplots(1, figsize=(12, 8))
            world.plot(ax=ax, facecolor="lightgray", edgecolor="gray")
            gdf.plot(ax=ax, color="#FF8C00", alpha=0.7, aspect="equal")
            plt.show()

    def visualize_elevation(self):
        """
        Visualize elevation requested from OpenAltimetry API using datashader based on cycles
        https://holoviz.org/tutorial/Large_Data.html

        Returns
        -------
        map_cycle, map_rgt + lineplot_rgt : Holoviews objects
            Holoviews data visualization elements
        """
        viz = Visualize(self)
        cycle_map, rgt_map = viz.viz_elevation()

        return cycle_map, rgt_map
