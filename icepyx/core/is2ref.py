import json
import warnings
from xml.etree import ElementTree as ET

import earthaccess
import h5py
import numpy as np
import requests

from icepyx.core.urls import COLLECTION_SEARCH_BASE_URL, EGI_BASE_URL

# ICESat-2 specific reference functions


def _get_concept_id(product, version):
    collections = earthaccess.search_datasets(
        short_name=product, version=version, cloud_hosted=True
    )
    if collections:
        return collections[0].concept_id()


def _validate_product(product):
    """
    Confirm a valid ICESat-2 product was specified
    """
    error_msg = (
        "A valid product string was not provided. "
        "Check user input, if given, or file metadata."
    )
    if isinstance(product, str):
        product = str.upper(product)
        assert product in [
            "ATL01",
            "ATL02",
            "ATL03",
            "ATL04",
            "ATL06",
            "ATL07",
            "ATL07QL",
            "ATL08",
            "ATL09",
            "ATL09QL",
            "ATL10",
            "ATL11",
            "ATL12",
            "ATL13",
            "ATL14",
            "ATL15",
            "ATL16",
            "ATL17",
            "ATL19",
            "ATL20",
            "ATL21",
            "ATL23",
        ], error_msg
    else:
        raise TypeError(error_msg)
    return product


def _validate_OA_product(product):
    """
    Confirm a valid ICESat-2 product was specified
    """
    if isinstance(product, str):
        product = str.upper(product)
        assert product in [
            "ATL06",
            "ATL07",
            "ATL08",
            "ATL10",
            "ATL12",
            "ATL13",
        ], (
            "Oops! Elevation visualization only supports products ATL06, ATL07, ATL08, ATL10, ATL12, ATL13; please try another product."
        )
    else:
        raise TypeError("Please enter a product string")
    return product


# DevNote: test for this function is commented out; dates in some of the values were causing the test to fail...
def about_product(prod):
    """
    Ping Earthdata to get metadata about the product of interest (the collection).

    See Also
    --------
    query.Query.product_all_info
    """

    response = requests.get(COLLECTION_SEARCH_BASE_URL, params={"short_name": prod})
    results = json.loads(response.content)
    return results


# DevGoal: use a mock of this output to test later functions, such as displaying options and widgets, etc.
# options to get customization options for ICESat-2 data (though could be used generally)
def _get_custom_options(session, product, version):
    """
    Get lists of what customization options are available for the product from NSIDC.
    """
    cust_options = {}

    # flagging for update/removal given removal of `.earthdata_login()`
    if session is None:
        raise ValueError(
            "Don't forget to log in to Earthdata using query.earthdata_login()"
        )

    capability_url = f"{EGI_BASE_URL}/capabilities/{product}.{version}.xml"
    response = session.get(capability_url)
    root = ET.fromstring(response.content)

    # collect lists with each service option
    subagent = [subset_agent.attrib for subset_agent in root.iter("SubsetAgent")]
    cust_options.update({"options": subagent})

    # reformatting
    formats = [Format.attrib for Format in root.iter("Format")]
    format_vals = [formats[i]["value"] for i in range(len(formats))]
    try:
        format_vals.remove("")
    except KeyError:
        # ATL23 does not have an empty value
        pass
    cust_options.update({"fileformats": format_vals})

    # reprojection only applicable on ICESat-2 L3B products.

    # reprojection options
    projections = [Projection.attrib for Projection in root.iter("Projection")]
    proj_vals = []
    for i in range(len(projections)):
        if (projections[i]["value"]) != "NO_CHANGE":
            proj_vals.append(projections[i]["value"])
    cust_options.update({"reprojectionONLY": proj_vals})

    # reformatting options that do not support reprojection
    exclformats_all = []
    for i in range(len(projections)):
        if "excludeFormat" in projections[i]:
            exclformats_str = projections[i]["excludeFormat"]
            exclformats_all.append(exclformats_str.split(","))
    exclformats_list = [
        item for sublist in exclformats_all for item in sublist
    ]  # list only unique formats
    no_proj = list(set(exclformats_list))
    cust_options.update({"noproj": no_proj})

    # reformatting options that support reprojection
    format_proj = []
    for i in range(len(format_vals)):
        if format_vals[i] not in no_proj:
            format_proj.append(format_vals[i])
    cust_options.update({"formatreproj": format_proj})

    # variable subsetting
    vars_raw = []

    def get_varlist(elem):
        childlist = list(elem)
        if len(childlist) == 0 and elem.tag == "SubsetVariable":
            vars_raw.append(elem.attrib["value"])
        for child in childlist:
            get_varlist(child)

    get_varlist(root)
    vars_vals = [
        v.replace(":", "/") if v.startswith("/") is False else v.replace("/:", "")
        for v in vars_raw
    ]
    cust_options.update({"variables": vars_vals})

    return cust_options


# DevGoal: populate this with default variable lists for all of the products!
# DevGoal: add a test for this function (to make sure it returns the right list, but also to deal with product not being in the list, though it should since it was checked as valid earlier...)
def _default_varlists(product):
    """
    Return a list of default variables to select and send to the NSIDC subsetter.
    """
    common_list = ["delta_time", "latitude", "longitude"]

    if product == "ATL06":
        return common_list + [
            "h_li",
            "h_li_sigma",
            "atl06_quality_summary",
            "segment_id",
            "sigma_geo_h",
            "x_atc",
            "y_atc",
            "seg_azimuth",
            "sigma_geo_at",
            "sigma_geo_xt",
            "dh_fit_dx",
            "dh_fit_dx_sigma",
            "h_mean",
            "dh_fit_dy",
            "h_rms_misfit",
            "h_robust_sprd",
            "n_fit_photons",
            "signal_selection_source",
            "snr_significance",
            "w_surface_window_final",
            "bsnow_conf",
            "bsnow_h",
            "cloud_flg_asr",
            "cloud_flg_atm",
            "r_eff",
            "tide_ocean",
        ]

    elif product == "ATL07":
        return common_list + [
            "seg_dist_x",
            "height_segment_height",
            "height_segment_length_seg",
            "height_segment_ssh_flag",
            "height_segment_type",
            "height_segment_quality",
            "height_segment_confidence",
        ]

    elif product == "ATL09":
        return common_list + [
            "bsnow_h",
            "bsnow_dens",
            "bsnow_con",
            "bsnow_psc",
            "bsnow_od",
            "cloud_flag_asr",
            "cloud_fold_flag",
            "cloud_flag_atm",
            "column_od_asr",
            "column_od_asr_qf",
            "layer_attr",
            "layer_bot",
            "layer_top",
            "layer_flag",
            "layer_dens",
            "layer_ib",
            "msw_flag",
            "prof_dist_x",
            "prof_dist_y",
            "apparent_surf_reflec",
        ]

    elif product == "ATL10":
        return common_list + [
            "seg_dist_x",
            "lead_height",
            "lead_length",
            "beam_fb_height",
            "beam_fb_length",
            "beam_fb_confidence",
            "beam_fb_quality_flag",
            "height_segment_height",
            "height_segment_length_seg",
            "height_segment_ssh_flag",
            "height_segment_type",
            "height_segment_confidence",
        ]

    elif product == "ATL11":
        return common_list + [
            "h_corr",
            "h_corr_sigma",
            "h_corr_sigma_systematic",
            "quality_summary",
        ]

    else:
        print(
            "THE REQUESTED PRODUCT DOES NOT YET HAVE A DEFAULT LIST SET UP. ONLY DELTA_TIME, LATITUDE, AND LONGITUDE WILL BE RETURNED"
        )
        return common_list


# Currently this function is used one-off, but if it needs to be done for a series of values,
# a faster version using pandas map (instead of apply) is available in SlideRule:
# https://github.com/SlideRuleEarth/sliderule/issues/388
# https://github.com/SlideRuleEarth/sliderule/commit/46cceac0e5f6d0a580933d399a6239bc911757f3
def gt2spot(gt, sc_orient):
    warnings.warn(
        "icepyx versions 0.8.0 and earlier used an incorrect spot number calculation."
        "As a result, computations depending on spot number may be incorrect and should be redone."
    )

    assert gt in [
        "gt1l",
        "gt1r",
        "gt2l",
        "gt2r",
        "gt3l",
        "gt3r",
    ], "An invalid ground track was found"

    gr_num = np.uint8(gt[2])
    gr_lr = gt[3]

    # spacecraft oriented forward
    if sc_orient == 1:
        if gr_num == 1:
            if gr_lr == "l":
                spot = 6
            elif gr_lr == "r":
                spot = 5
        elif gr_num == 2:
            if gr_lr == "l":
                spot = 4
            elif gr_lr == "r":
                spot = 3
        elif gr_num == 3:
            if gr_lr == "l":
                spot = 2
            elif gr_lr == "r":
                spot = 1

    # spacecraft oriented backward
    elif sc_orient == 0:
        if gr_num == 1:
            if gr_lr == "l":
                spot = 1
            elif gr_lr == "r":
                spot = 2
        elif gr_num == 2:
            if gr_lr == "l":
                spot = 3
            elif gr_lr == "r":
                spot = 4
        elif gr_num == 3:
            if gr_lr == "l":
                spot = 5
            elif gr_lr == "r":
                spot = 6

    if "spot" not in locals():
        raise ValueError("Could not compute the spot number.")

    return np.uint8(spot)


def latest_version(product):
    """
    Determine the most recent version available for the given product.

    Examples
    --------
    >>> latest_version('ATL03')
    '006'
    """
    _about_product = about_product(product)

    return max([entry["version_id"] for entry in _about_product["feed"]["entry"]])


def extract_product(filepath, auth=None):
    """
    Read the product type from the metadata of the file. Valid for local or s3 files, but must
    provide an auth object if reading from s3. Return the product as a string.

    Parameters
    ----------
    filepath: string
        local or remote location of a file. Could be a local string or an s3 filepath
    auth: earthaccess.auth.Auth, default None
        An earthaccess authentication object. Optional, but necessary if accessing data in an
        s3 bucket.
    """
    # Generate a file reader object relevant for the file location
    if filepath.startswith("s3"):
        if not auth:
            raise AttributeError(
                "Must provide credentials to `auth` if accessing s3 data"
            )
        # Read the s3 file
        s3 = earthaccess.get_s3fs_session(daac="NSIDC")
        f = h5py.File(s3.open(filepath, "rb"))
    else:
        # Otherwise assume a local filepath. Read with h5py.
        f = h5py.File(filepath, "r")

    # Extract the product information
    try:
        product = f.attrs["short_name"]
        if isinstance(product, bytes):
            # For most products the short name is stored in a bytes string
            product = product.decode()
        elif isinstance(product, np.ndarray):
            # ATL14 saves the short_name as an array ['ATL14']
            product = product[0]
        product = _validate_product(product)
    except KeyError as e:
        raise Exception(
            "Unable to parse the product name from file metadata"
        ).with_traceback(e.__traceback__)

    # Close the file reader
    f.close()
    return product


def extract_version(filepath, auth=None):
    """
    Read the version from the metadata of the file. Valid for local or s3 files, but must
    provide an auth object if reading from s3. Return the version as a string.

    Parameters
    ----------
    filepath: string
        local or remote location of a file. Could be a local string or an s3 filepath
    auth: earthaccess.auth.Auth, default None
        An earthaccess authentication object. Optional, but necessary if accessing data in an
        s3 bucket.
    """
    # Generate a file reader object relevant for the file location
    if filepath.startswith("s3"):
        if not auth:
            raise AttributeError(
                "Must provide credentials to `auth` if accessing s3 data"
            )
        # Read the s3 file
        s3 = earthaccess.get_s3fs_session(daac="NSIDC")
        f = h5py.File(s3.open(filepath, "rb"))
    else:
        # Otherwise assume a local filepath. Read with h5py.
        f = h5py.File(filepath, "r")

    # Read the version information
    try:
        version = f["METADATA"]["DatasetIdentification"].attrs["VersionID"]
        if isinstance(version, np.ndarray):
            # ATL14 stores the version as an array ['00x']
            version = version[0]
        if isinstance(version, bytes):
            version = version.decode()

    except KeyError as e:
        raise Exception(
            "Unable to parse the version from file metadata"
        ).with_traceback(e.__traceback__)

    # catch cases where the version number is an invalid string
    # e.g. a VersionID of "SET_BY_PGE", causing issues where version needs to be a valid number
    try:
        float(version)
    except ValueError:
        raise Exception(
            "There is an underlying issue with the version information"
            "provided in the metadata of this file."
            "Consider setting the version manually for further processing."
        )

    # Close the file reader
    f.close()
    return version
