import os
import warnings

from deprecated import deprecated
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient

# DevGoal: need to update the spatial_extent docstring to describe coordinate order for input


def geodataframe(extent_type, spatial_extent, file=False, xdateline=None):
    """
    Return a geodataframe of the spatial extent

    Parameters
    ----------
    extent_type : string
        One of 'bounding_box' or 'polygon', indicating what type of input the spatial extent is

    spatial_extent : string or list
        A list containing the spatial extent OR a string containing a filename.
        If file is False, spatial_extent should be a
        list of coordinates in decimal degrees of [lower-left-longitude,
        lower-left-latitute, upper-right-longitude, upper-right-latitude] or
        [longitude1, latitude1, longitude2, latitude2, ... longitude_n,latitude_n, longitude1,latitude1].

        If file is True, spatial_extent is a string containing the full file path and filename to the
        file containing the desired spatial extent.

    file : boolean, default False
        Indication for whether the spatial_extent string is a filename or coordinate list

    Returns
    -------
    gdf : GeoDataFrame
        Returns a GeoPandas GeoDataFrame containing the spatial extent.
        The GeoDataFrame will have only one entry unless a geospatial file
        was submitted.

    See Also
    --------
    icepyx.Query

    Examples
    --------
    >>> reg_a = ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-20','2019-02-28'])
    >>> gdf = geodataframe(reg_a.spatial.extent_type, reg_a.spatial.extent)
    >>> gdf.geometry
    0    POLYGON ((-48 68, -48 71, -55 71, -55 68, -48 ...
    Name: geometry, dtype: geometry
    """

    if xdateline is not None:
        xdateline = xdateline
    elif file:
        pass
    else:
        xdateline = check_dateline(extent_type, spatial_extent)
    # print("this should cross the dateline:" + str(xdateline))

    if extent_type == "bounding_box":
        if xdateline is True:
            cartesian_lons = [i if i > 0 else i + 360 for i in spatial_extent[0:-1:2]]
            cartesian_spatial_extent = [
                item
                for pair in zip(cartesian_lons, spatial_extent[1::2])
                for item in pair
            ]
            bbox = box(*cartesian_spatial_extent)
        else:
            bbox = box(*spatial_extent)

        # TODO: test case that ensures gdf is constructed as expected (correct coords, order, etc.)
        gdf = gpd.GeoDataFrame(geometry=[bbox], crs="epsg:4326")

    # DevGoal: Currently this if/else within this elif are not tested...
    # DevGoal: the crs setting and management needs to be improved

    elif extent_type == "polygon" and file is False:
        # if spatial_extent is already a Polygon
        if isinstance(spatial_extent, Polygon):
            spatial_extent_geom = spatial_extent

        # else, spatial_extent must be a list of floats (or list of tuples of floats)
        else:
            if xdateline is True:
                cartesian_lons = [
                    i if i > 0 else i + 360 for i in spatial_extent[0:-1:2]
                ]
                spatial_extent = [
                    item
                    for pair in zip(cartesian_lons, spatial_extent[1::2])
                    for item in pair
                ]

            spatial_extent_geom = Polygon(
                # syntax of dbl colon is- "start:stop:steps"
                # 0::2 = start at 0, grab every other coord after
                # 1::2 = start at 1, grab every other coord after
                zip(spatial_extent[0::2], spatial_extent[1::2])
            )  # spatial_extent
        # TODO: check if the crs param should always just be epsg:4326 for everything OR if it should be a parameter
        gdf = gpd.GeoDataFrame(
            index=[0], crs="epsg:4326", geometry=[spatial_extent_geom]
        )

    # If extent_type is a polygon AND from a file, create a geopandas geodataframe from it
    # DevGoal: Currently this elif isn't tested...
    elif extent_type == "polygon" and file is True:
        gdf = gpd.read_file(spatial_extent)

    else:
        raise TypeError(
            f"Your spatial extent type ({extent_type}) is not an accepted "
            "input and a geodataframe cannot be constructed"
        )

    return gdf


def check_dateline(extent_type, spatial_extent):
    """
    Check if a bounding box or polygon input cross the dateline.

    Parameters
    ----------
    extent_type : string
        One of 'bounding_box' or 'polygon', indicating what type of input the spatial extent is

    spatial_extent : list
        A list containing the spatial extent as
        coordinates in decimal degrees of
        [longitude1, latitude1, longitude2, latitude2, ... longitude_n,latitude_n, longitude1,latitude1].


    Returns
    -------
    boolean
        indicating whether or not the spatial extent crosses the dateline.
    """

    if extent_type == "bounding_box":
        if spatial_extent[0] > spatial_extent[2]:
            # if lower left lon is larger then upper right lon, verify the values are crossing the dateline
            assert spatial_extent[0] - 360 <= spatial_extent[2]

            warnings.warn(
                "Your bounding box was identified as crossing the dateline."
                "If this is not correct, please add `xdateline=False` to your `ipx.Query`"
            )
            return True

        else:
            return False

    # this works properly, but limits the user to at most 270 deg longitude...
    elif extent_type == "polygon":
        assert not isinstance(spatial_extent[0], (list, tuple)), (
            "Your polygon list is the wrong format for this function."
        )
        lonlist = spatial_extent[0:-1:2]
        if np.any(
            [abs(lonlist[i] - lonlist[i + 1]) > 270 for i in range(len(lonlist) - 1)]
        ):
            warnings.warn(
                "Your polygon was identified as crossing the dateline."
                "If this is not correct, please add `xdateline=False` to your `ipx.Query`"
            )
            return True
        else:
            return False


def validate_bounding_box(spatial_extent):
    """
    Validates the spatial_extent parameter as a bounding box.

    If the spatial_extent is a valid bounding box, returns a tuple containing the Spatial object parameters
    for the bounding box; otherwise, throw an error containing the reason the bounding box is invalid.

    Parameters
    ----------
    spatial_extent: list or np.ndarray
                    A list or np.ndarray of strings, numerics, or tuples
                    representing bounding box coordinates in decimal degrees.

                    Must be provided in the order:
                    [lower-left-longitude, lower-left-latitude,
                    upper-right-longitude, upper-right-latitude])
    """

    # Latitude must be between -90 and 90 (inclusive); check for this here
    assert -90 <= spatial_extent[1] <= 90, (
        "Invalid latitude value (must be between -90 and 90, inclusive)"
    )
    assert -90 <= spatial_extent[3] <= 90, (
        "Invalid latitude value (must be between -90 and 90, inclusive)"
    )

    assert -180 <= spatial_extent[0] <= 180, (
        "Invalid longitude value (must be between -180 and 180, inclusive)"
    )
    assert -180 <= spatial_extent[2] <= 180, (
        "Invalid longitude value (must be between -180 and 180, inclusive)"
    )

    # If the lower left latitude is greater than the upper right latitude, throw an error
    assert spatial_extent[1] <= spatial_extent[3], "Invalid bounding box latitudes"

    spatial_extent = [float(x) for x in spatial_extent]

    return "bounding_box", spatial_extent, None


def validate_polygon_pairs(spatial_extent):
    """
    Validates the spatial_extent parameter as a polygon from coordinate pairs.

    If the spatial_extent is a valid polygon, returns a tuple containing the Spatial object parameters
    for the polygon;

    otherwise, throw an error containing the reason the polygon is invalid.

    Parameters
    ----------
    spatial_extent: list or np.ndarray

                    A list or np.ndarray of tuples representing polygon coordinate pairs in decimal degrees in the order:
                    [(longitude1, latitude1), (longitude2, latitude2), ...
                    ... (longitude_n,latitude_n), (longitude1,latitude1)]

                    If the first and last coordinate pairs are NOT equal,
                    the polygon will be closed automatically (last point will be connected to the first point).
    """
    # Check to make sure all elements of spatial_extent are coordinate pairs; if not, raise an error
    if any(len(i) != 2 for i in spatial_extent):
        raise ValueError(
            "Each element in spatial_extent should be a list or tuple of length 2"
        )

    # If there are less than 4 vertices, raise an error
    assert len(spatial_extent) >= 4, "Your spatial extent polygon has too few vertices"

    if (spatial_extent[0][0] != spatial_extent[-1][0]) or (
        spatial_extent[0][1] != spatial_extent[-1][1]
    ):
        # Throw a warning
        warnings.warn(
            "WARNING: Polygon's first and last point's coordinates differ,"
            " closing the polygon automatically."
        )
        # Add starting long/lat to end
        if isinstance(spatial_extent, list):
            # use list.append() method
            spatial_extent.append(spatial_extent[0])

        elif isinstance(spatial_extent, np.ndarray):
            # use np.insert() method
            spatial_extent = np.insert(
                spatial_extent, len(spatial_extent), spatial_extent[0]
            )

    polygon = (",".join([str(c) for xy in spatial_extent for c in xy])).split(",")

    # make all elements of polygon floats
    polygon = [float(i) for i in polygon]

    return "polygon", polygon, None


def validate_polygon_list(spatial_extent):
    """
    Validates the spatial_extent parameter as a polygon from a list of coordinates.

    If the spatial_extent is a valid polygon, returns a tuple containing the Spatial object parameters
    for the polygon;

    otherwise, throw an error containing the reason the polygon is invalid.

    Parameters
    ----------
    spatial_extent: list or np.ndarray
                    A list or np.ndarray of strings, numerics, or tuples representing polygon coordinates,
                    provided as coordinate pairs in decimal degrees in the order:
                    [longitude1, latitude1, longitude2, latitude2, ...
                    ... longitude_n,latitude_n, longitude1,latitude1]

                    If the first and last coordinate pairs are NOT equal,
                    the polygon will be closed automatically (last point will be connected to the first point).
    """

    # user-entered polygon as a single list of lon and lat coordinates
    assert len(spatial_extent) >= 8, "Your spatial extent polygon has too few vertices"
    assert len(spatial_extent) % 2 == 0, (
        "Your spatial extent polygon list should have an even number of entries"
    )

    if (spatial_extent[0] != spatial_extent[-2]) or (
        spatial_extent[1] != spatial_extent[-1]
    ):
        warnings.warn(
            "WARNING: Polygon's first and last point's coordinates differ,"
            " closing the polygon automatically."
        )

        # Add starting long/lat to end
        if isinstance(spatial_extent, list):
            # use list.append() method
            spatial_extent.append(spatial_extent[0])
            spatial_extent.append(spatial_extent[1])

        elif isinstance(spatial_extent, np.ndarray):
            # use np.insert() method
            spatial_extent = np.insert(
                spatial_extent, len(spatial_extent), spatial_extent[0]
            )
            spatial_extent = np.insert(
                spatial_extent, len(spatial_extent), spatial_extent[1]
            )

    polygon = [float(i) for i in spatial_extent]

    return "polygon", polygon, None


def validate_polygon_file(spatial_extent):
    """
    Validates the spatial_extent parameter as a polygon from a file.

    If the spatial_extent parameter contains a valid polygon,
    returns a tuple containing the Spatial object parameters for the polygon;

    otherwise, throw an error containing the reason the polygon/polygon file is invalid.

    Parameters
    ----------
    spatial_extent: string
                     A string representing a geospatial polygon file (kml, shp, gpkg)
                     * must provide full file path
                     * recommended for file to only contain 1 polygon.
                         * if multiple polygons, only the first polygon is selected at this time.

    """

    # Check if the filename path exists; if not, throw an error
    # print("print statements work \n")
    # print("SPATIAL EXTENT: " + spatial_extent + "\n")
    assert os.path.exists(spatial_extent), (
        "Check that the path and filename of your geometry file are correct"
    )

    # DevGoal: more robust polygon inputting (see Bruce's code):
    # correct for clockwise/counterclockwise coordinates, deal with simplification, etc.

    if spatial_extent.split(".")[-1] in ["kml", "shp", "gpkg"]:
        extent_type = "polygon"
        gdf = geodataframe(extent_type, spatial_extent, file=True)

        return "polygon", gdf, spatial_extent

    else:
        raise TypeError("Input spatial extent file must be a kml, shp, or gpkg")


class Spatial:
    def __init__(self, spatial_extent, **kwarg):
        """
        Validates input from "spatial_extent" argument, then creates a Spatial object with validated inputs
        as properties of the object.

        Spatial objects are to be used by icepyx.Query to store validated geospatial information required by the Query.

        Parameters
        ----------
        spatial_extent : list or string
            * list of coordinates
             (stored in a list of strings, list of numerics, list of tuples, OR np.ndarray) as one of:
                * bounding box
                    * provided in the order: [lower-left-longitude, lower-left-latitude,
                                             upper-right-longitude, upper-right-latitude].)
                * polygon
                    * provided as coordinate pairs in decimal degrees as one of:
                        * [(longitude1, latitude1), (longitude2, latitude2), ...
                          ... (longitude_n,latitude_n), (longitude1,latitude1)]
                        * [longitude1, latitude1, longitude2, latitude2,
                        ... longitude_n,latitude_n, longitude1,latitude1].
                    * NOTE: If the first and last coordinate pairs are NOT equal,
                    the polygon will be closed automatically (last point will be connected to the first point).
            * string representing a geospatial polygon file (kml, shp, gpkg)
                * full file path
                * recommended for file to only contain 1 polygon; if multiple, only selects first polygon rn

        xdateline : boolean, default None
            Optional keyword argument to let user specify whether the spatial input crosses the dateline or not.


        See Also
        --------
        icepyx.Query


        Examples
        --------
        Initializing Spatial with a bounding box.

        >>> reg_a_bbox = [-55, 68, -48, 71]
        >>> reg_a = Spatial(reg_a_bbox)
        >>> print(reg_a)
        Extent type: bounding_box
        Coordinates: [-55.0, 68.0, -48.0, 71.0]

        Initializing Query with a list of polygon vertex coordinate pairs.

        >>> reg_a_poly = [(-55, 68), (-55, 71), (-48, 71), (-48, 68), (-55, 68)]
        >>> reg_a = Spatial(reg_a_poly)
        >>> print(reg_a)
        Extent type: polygon
        Coordinates: [-55.0, 68.0, -55.0, 71.0, -48.0, 71.0, -48.0, 68.0, -55.0, 68.0]

        Initializing Query with a geospatial polygon file.

        >>> from pathlib import Path
        >>> aoi = Path('./doc/source/example_notebooks/supporting_files/simple_test_poly.gpkg').resolve()
        >>> reg_a = Spatial(str(aoi))
        >>> print(reg_a) # doctest: +SKIP
        Extent Type: polygon
        Source file: ./doc/source/example_notebooks/supporting_files/simple_test_poly.gpkg
        Coordinates: [-55.0, 68.0, -55.0, 71.0, -48.0, 71.0, -48.0, 68.0, -55.0, 68.0]
        """

        scalar_types = (int, float, np.int64)

        # Check if spatial_extent is a list of coordinates (bounding box or polygon)
        if isinstance(spatial_extent, (list, np.ndarray)):
            # bounding box
            if len(spatial_extent) == 4 and all(
                isinstance(i, scalar_types) for i in spatial_extent
            ):
                (
                    self._ext_type,
                    self._spatial_ext,
                    self._geom_file,
                ) = validate_bounding_box(spatial_extent)

            # polygon (as list of lon, lat coordinate pairs, in tuples)
            elif all(
                type(i) in [list, tuple, np.ndarray] for i in spatial_extent
            ) and all(
                all(isinstance(i[j], scalar_types) for j in range(len(i)))
                for i in spatial_extent
            ):
                (
                    self._ext_type,
                    self._spatial_ext,
                    self._geom_file,
                ) = validate_polygon_pairs(spatial_extent)

            # polygon (as list of lon, lat coordinate pairs, single "flat" list)
            elif all(isinstance(i, scalar_types) for i in spatial_extent):
                (
                    self._ext_type,
                    self._spatial_ext,
                    self._geom_file,
                ) = validate_polygon_list(spatial_extent)
            else:
                # TODO: Change this warning to be like "usage", tell user possible accepted input types
                raise ValueError(
                    "Your spatial extent does not meet minimum input criteria or the input format is not correct"
                )

        # Check if spatial_extent is a string (i.e. a (potential) filename)
        elif isinstance(spatial_extent, str):
            self._ext_type, self._gdf_spat, self._geom_file = validate_polygon_file(
                spatial_extent
            )

            # TODO: assess if it's necessary to have a value for _spatial_extent if the input is a file (since it can be plotted from the gdf)
            extpoly = self._gdf_spat.geometry.unary_union.boundary

            try:
                arrpoly = (
                    ",".join([str(c) for xy in zip(*extpoly.coords.xy) for c in xy])
                ).split(",")
            except NotImplementedError:
                arrpoly = (
                    ",".join(
                        [
                            str(c)
                            for xy in zip(*extpoly.envelope.boundary.coords.xy)
                            for c in xy
                        ]
                    )
                ).split(",")

            self._spatial_ext = [float(i) for i in arrpoly]

        # check for cross dateline keyword submission
        if "xdateline" in kwarg:
            self._xdateln = kwarg["xdateline"]
            assert self._xdateln in [
                True,
                False,
            ], "Your 'xdateline' value is invalid. It must be boolean."

    def __str__(self):
        if self._geom_file is not None:
            return "Extent type: {0}\nSource file: {1}\nCoordinates: {2}".format(
                self._ext_type, self._geom_file, self._spatial_ext
            )
        else:
            return "Extent type: {0}\nCoordinates: {1}".format(
                self._ext_type, self._spatial_ext
            )

    @property
    def extent(self):
        """
        Return the coordinates of the spatial extent of the Spatial object.

        The result will be returned as an array.
        For input geometry files with multiple features, the boundary of the
        the unary union of all features is returned.

        Returns
        -------
        spatial extent : array
            An array of bounding coordinates.
        """

        return self._spatial_ext

    @property
    def extent_as_gdf(self):
        """
        Return the spatial extent of the query object as a GeoPandas GeoDataframe.

        Returns
        -------
        extent_gdf : GeoDataframe
            A GeoDataframe containing the spatial region of interest.
        """

        # TODO: test this
        xdateln = self._xdateln if hasattr(self, "_xdateln") else None

        if not hasattr(self, "_gdf_spat"):
            if self._geom_file is not None:
                self._gdf_spat = geodataframe(
                    self._ext_type, self._spatial_ext, file=True, xdateline=xdateln
                )
            else:
                self._gdf_spat = geodataframe(
                    self._ext_type, self._spatial_ext, xdateline=xdateln
                )

        return self._gdf_spat

    @property
    def extent_type(self):
        """
        Return the extent type of the Spatial object as a string.

        Examples
        --------
        >>> reg_a = Spatial([-55, 68, -48, 71])
        >>> reg_a.extent_type
        'bounding_box'

        >>> reg_a = Spatial([(-55, 68), (-55, 71), (-48, 71), (-48, 68), (-55, 68)])
        >>> reg_a.extent_type
        'polygon'
        """

        return self._ext_type

    @property
    def extent_file(self):
        """
        Return the path to the geospatial polygon file containing the Spatial object's spatial extent.
        If the spatial extent did not come from a file (i.e. user entered list of coordinates), this will return None.

        Examples
        --------
        >>> reg_a = Spatial([-55, 68, -48, 71])
        >>> reg_a.extent_file


        >>> from pathlib import Path
        >>> reg_a = Spatial(str(Path('./doc/source/example_notebooks/supporting_files/simple_test_poly.gpkg').resolve()))
        >>> reg_a.extent_file # doctest: +SKIP
        ./doc/source/example_notebooks/supporting_files/simple_test_poly.gpkg
        """
        return self._geom_file

    # ----------------------------------------------------------------------
    # Methods

    # TODO: can use this docstring as a todo list
    def fmt_for_CMR(self):
        """
        Format the spatial extent for NASA's Common Metadata Repository (CMR) API.

        CMR spatial inputs must be formatted a specific way.
        This method formats the given spatial extent to be a valid submission.
        For large/complex polygons, this includes simplifying the polygon (NOTE: currently not all polygons are simplified enough).
        Coordinates will be properly ordered, and the required string formatting applied.
        For small regions, a buffer may be added.

        Returns
        -------
        string
            Properly formatted string of spatial data for submission to CMR API.


        """
        # CMR keywords: ['bounding_box', 'polygon']
        if self._ext_type == "bounding_box":
            cmr_extent = ",".join(map(str, self._spatial_ext))

        elif self._ext_type == "polygon":
            poly = self.extent_as_gdf.geometry

            if any(
                geomtype in ["MultiPoint", "MultiLineString", "MultiPolygon"]
                for geomtype in poly.geom_type
            ):
                poly = poly.convex_hull

            poly = poly.unary_union

            # Simplify polygon. The larger the tolerance value, the more simplified the polygon. See Bruce Wallin's function to do this
            poly = poly.simplify(0.05, preserve_topology=True)
            poly = orient(poly, sign=1.0)

            # Format dictionary to polygon coordinate pairs for API submission
            polygon = (
                ",".join([str(c) for xy in zip(*poly.exterior.coords.xy) for c in xy])
            ).split(",")
            extent = [float(i) for i in polygon]

            # TODO: explore how this will be impacted if the polygon is read in from a shapefile and crosses the dateline
            if hasattr(self, "_xdateln") and self._xdateln is True:
                neg_lons = [i if i < 181.0 else i - 360 for i in extent[0:-1:2]]
                extent = [item for pair in zip(neg_lons, extent[1::2]) for item in pair]

            cmr_extent = ",".join(map(str, extent))

        return cmr_extent

    @deprecated("Use fmt_for_CMR instead")
    def fmt_for_EGI(self):
        """
        WARNING: This method is deprecated. Use fmt_for_CMR instead.
        Format the spatial extent input into a subsetting key value for submission to EGI (the NSIDC DAAC API).

        EGI spatial inputs must be formatted a specific way.
        This method formats the given spatial extent to be a valid submission.
        DevGoal: For large/complex polygons, this includes simplifying the polygon.
        Coordinates will be properly ordered, and the required string formatting applied.

        Returns
        -------
        string
            Properly formatted json string for submission to CMR
        """
        return self.fmt_for_CMR()
