"""Generate and format information for submitting to API (CMR and NSIDC)."""

import datetime as dt
from typing import Any, Generic, Literal, Optional, TypeVar, Union

from icepyx.core.exceptions import ExhaustiveTypeGuardException, TypeGuardException
from icepyx.core.types import (
    CMRParams,
    CMRParamsWithBbox,
    CMRParamsWithPolygon,
)

# ----------------------------------------------------------------------
# parameter-specific formatting for display
# or input to a set of API parameters (CMR or NSIDC)


def _fmt_temporal(start, end, key):
    """
    Format the start and end dates and times into a temporal CMR search
    or subsetting key value.

    Parameters
    ----------
    start : date time object
        Start date and time for the period of interest.
    end : date time object
        End date and time for the period of interest.
    key : string
        Dictionary key, entered as a string, indicating which temporal format is needed.
        Must be one of ['temporal','time'] for data searching and subsetting, respectively.

    Returns
    -------
    dictionary with properly formatted temporal parameter for CMR search or subsetting
    """

    assert isinstance(start, dt.datetime)
    assert isinstance(end, dt.datetime)

    if key == "temporal":
        fmt_timerange = (
            start.strftime("%Y-%m-%dT%H:%M:%SZ")
            + ","
            + end.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
    elif key == "time":
        fmt_timerange = (
            start.strftime("%Y-%m-%dT%H:%M:%S")
            + ","
            + end.strftime("%Y-%m-%dT%H:%M:%S")
        )
    else:
        raise ValueError("An invalid time key was submitted for formatting.")

    return {key: fmt_timerange}


def _fmt_readable_granules(dset, **kwds):
    """
    Create list of readable granule names for CMR queries

    Parameters
    ----------
    cycles : list
        List of 91-day orbital cycle strings to query
    tracks : list
        List of Reference Ground Track (RGT) strings to query
    files : list
        List of full or partial file name strings to query

    Returns
    -------
    list of readable granule names for CMR query
    """
    # copy keyword arguments if valid (not None or empty lists)
    kwargs = {k: v for k, v in kwds.items() if v}
    # list of readable granule names
    readable_granule_list = []
    # if querying either by 91-day orbital cycle or RGT
    if "cycles" in kwargs or "tracks" in kwargs:
        # default character wildcards for cycles and tracks
        kwargs.setdefault("cycles", ["??"])
        kwargs.setdefault("tracks", ["????"])
        # for each available cycle of interest
        for c in kwargs["cycles"]:
            # for each available track of interest
            for t in kwargs["tracks"]:
                # use single character wildcards "?" for date strings
                # and ATLAS granule region number
                if dset in ("ATL07", "ATL10", "ATL20", "ATL21"):
                    granule_name = "{0}-??_{1}_{2}{3}??_*".format(dset, 14 * "?", t, c)
                elif dset in ("ATL11",):
                    granule_name = "{0}_{1}??_*".format(dset, t)
                else:
                    granule_name = "{0}_{1}_{2}{3}??_*".format(dset, 14 * "?", t, c)
                # append the granule
                readable_granule_list.append(granule_name)
    # extend with explicitly named files (full or partial)
    kwargs.setdefault("files", [])
    readable_granule_list.extend(kwargs["files"])
    return readable_granule_list


def _fmt_var_subset_list(vdict):
    """
    Return the NSIDC-API subsetter formatted coverage string for variable subset request.

    Parameters
    ----------
    vdict : dictionary
        Dictionary containing variable names as keys with values containing a list of
        paths to those variables (so each variable key may have multiple paths, e.g. for
        multiple beams)
    """

    subcover = ""
    for vn in vdict:
        vpaths = vdict[vn]
        for vpath in vpaths:
            subcover += "/" + vpath + ","

    return subcover[:-1]


def combine_params(*param_dicts):
    """
    Combine multiple dictionaries into one.

    Merging is performed in sequence using `dict.update()`; dictionaries later in the
    list overwrite those earlier.

    Parameters
    ----------
    params : dictionaries
        Unlimited number of dictionaries to combine

    Returns
    -------
    A single dictionary of all input dictionaries combined

    Examples
    --------
    >>> CMRparams = {'temporal': '2019-02-20T00:00:00Z,2019-02-28T23:59:59Z', 'bounding_box': '-55,68,-48,71'}
    >>> reqparams = {'short_name': 'ATL06', 'version': '002', 'page_size': 2000, 'page_num': 1}
    >>> ipx.core.APIformatting.combine_params(CMRparams, reqparams)
    {'temporal': '2019-02-20T00:00:00Z,2019-02-28T23:59:59Z',
    'bounding_box': '-55,68,-48,71',
    'short_name': 'ATL06',
    'version': '002',
    'page_size': 2000,
    'page_num': 1}
    """
    params = {}
    for dictionary in param_dicts:
        params.update(dictionary)
    return params


def to_string(params):
    """
    Combine a parameter dictionary into a single url string

    Parameters
    ----------
    params : dictionary

    Returns
    -------
    url string of input dictionary (not encoded)

    Examples
    --------
    >>> CMRparams = {'temporal': '2019-02-20T00:00:00Z,2019-02-28T23:59:59Z',
    ...             'bounding_box': '-55,68,-48,71'}
    >>> reqparams = {'short_name': 'ATL06', 'version': '002', 'page_size': 2000, 'page_num': 1}
    >>> params = ipx.core.APIformatting.combine_params(CMRparams, reqparams)
    >>> ipx.core.APIformatting.to_string(params)
    'temporal=2019-02-20T00:00:00Z,2019-02-28T23:59:59Z&bounding_box=-55,68,-48,71&short_name=ATL06&version=002&page_size=2000&page_num=1'
    """
    param_list = []
    for k, v in params.items():
        if isinstance(v, list):
            for i in v:
                param_list.append(k + "=" + i)
        else:
            param_list.append(k + "=" + str(v))
    # return the parameter string
    return "&".join(param_list)


ParameterType = Literal["CMR", "required", "subset"]
# DevGoal: When Python 3.12 is minimum supported version, migrate to PEP695 style
T = TypeVar("T", bound=ParameterType)


class _FmtedKeysDescriptor:
    """Enable the Parameters class' fmted_keys property to be typechecked correctly.

    See: https://github.com/microsoft/pyright/issues/3071#issuecomment-1043978070
    """

    def __get__(
        self,
        instance: "Parameters",
        owner: Any,
    ) -> Union[CMRParams, CMRParamsWithBbox, CMRParamsWithPolygon, dict[str, Any]]:
        """
        Returns the dictionary of formatted keys associated with the
        parameter object.
        """
        return instance._fmted_keys  # pyright: ignore[reportReturnType]


# ----------------------------------------------------------------------
# DevNote: Currently, this class is not tested!!
# DevGoal: this could be expanded, similar to the variables class, to provide users with valid options if need be
# DevGoal: currently this does not do much by way of checking/formatting of other subsetting options (reprojection or formats)
# it would be great to incorporate that so that people can't just feed any keywords in...
class Parameters(Generic[T]):
    """
    Build and update the parameter lists needed to submit a data order

    Parameters
    ----------
    partype : string
        Type of parameter list. Must be one of ['CMR','required','subset']

    values : dictionary, default None
        Dictionary of already-formatted parameters, if there are any, to avoid
        re-creating them.

    reqtype : string, default None
        For `partype=='required'`, indicates which parameters are required based
        on the type of query. Must be one of ['search','download']
    """

    partype: T
    _reqtype: Optional[Literal["search", "download"]]
    fmted_keys = _FmtedKeysDescriptor()

    def __init__(
        self,
        partype: T,
        values: Optional[dict] = None,
        reqtype: Optional[Literal["search", "download"]] = None,
    ):
        assert partype in [
            "CMR",
            "required",
            "subset",
        ], "You need to submit a valid parameter type."
        self.partype = partype

        if partype == "required":
            assert reqtype in [
                "search",
                "download",
            ], "A valid require parameter type is needed"
        self._reqtype = reqtype

        self._fmted_keys = values if values is not None else {}

    @property
    def poss_keys(self) -> dict[str, list[str]]:
        """
        Returns a list of possible input keys for the given parameter object.
        Possible input keys depend on the parameter type (partype).
        """

        if self.partype == "CMR":
            return {
                "spatial": ["bounding_box", "polygon"],
                "optional": [
                    "temporal",
                    "options[readable_granule_name][pattern]",
                    "options[spatial][or]",
                    "readable_granule_name[]",
                ],
            }
        elif self.partype == "required":
            return {
                "search": ["short_name", "version", "page_size"],
                "download": [
                    "short_name",
                    "version",
                    "page_size",
                    "page_num",
                    "request_mode",
                    "token",
                    "email",
                    "include_meta",
                    "client_string",
                ],
            }
        elif self.partype == "subset":
            return {
                "spatial": ["bbox", "Boundingshape"],
                "optional": [
                    "time",
                    "format",
                    "projection",
                    "projection_parameters",
                    "Coverage",
                ],
            }
        else:
            raise ExhaustiveTypeGuardException

    # @property
    # def wanted_keys(self):
    #     if not hasattr(_wanted):
    #         self._wanted = []

    #     return self._wanted

    def _check_valid_keys(self) -> None:
        """
        Checks that any keys passed in with values are valid keys.
        """

        # if self._wanted == None:
        #     raise ValueError("No desired parameter list was passed")

        val_list = list({val for lis in self.poss_keys.values() for val in lis})

        for key in self.fmted_keys:  # pyright: ignore[reportAttributeAccessIssue]
            assert key in val_list, (
                "An invalid key (" + key + ") was passed. Please remove it using `del`"
            )

    # DevNote: can check_req_values and check_values be combined?
    def check_req_values(self) -> bool:
        """
        Check that all of the required keys have values, if the key was passed in with
        the values parameter.
        """

        assert self.partype == "required", (
            "You cannot call this function for your parameter type"
        )

        if not self._reqtype:
            raise TypeGuardException

        reqkeys = self.poss_keys[self._reqtype]

        if all(keys in self.fmted_keys for keys in reqkeys):  # pyright: ignore[reportAttributeAccessIssue]
            assert all(
                self.fmted_keys.get(key, -9999) != -9999  # pyright: ignore[reportAttributeAccessIssue]
                for key in reqkeys
            ), "One of your formatted parameters is missing a value"
            return True
        else:
            return False

    def check_values(self) -> bool:
        """
        Check that the non-required keys have values, if the key was
        passed in with the values parameter.
        """
        assert self.partype != "required", (
            "You cannot call this function for your parameter type"
        )

        spatial_keys = self.poss_keys["spatial"]

        # not the most robust check, but better than nothing...
        if any(keys in self._fmted_keys for keys in spatial_keys):
            assert any(
                self.fmted_keys.get(key, -9999) != -9999  # pyright: ignore[reportAttributeAccessIssue]
                for key in spatial_keys
            ), "One of your formatted parameters is missing a value"
            return True
        else:
            return False

    def build_params(self, **kwargs) -> None:
        """
        Build the parameter dictionary of formatted key:value pairs for submission to NSIDC
        in the data request.

        Parameters
        ----------
        **kwargs
            Keyword inputs containing the needed information to build the parameter list, depending
            on parameter type, if the already formatted key:value is not submitted as a kwarg.
            May include optional keyword arguments to be passed to the subsetter.
            Valid keywords are time, bbox OR Boundingshape, format, projection,
            projection_parameters, and Coverage.

            Keyword argument inputs for 'CMR' may include:
            start, end, extent_type, spatial_extent
            Keyword argument inputs for 'required' may include:
            product or short_name, version, page_size, page_num,
            request_mode, include_meta, client_string
            Keyword argument inputs for 'subset' may include:
            geom_filepath, start, end, extent_type, spatial_extent

        """

        if not kwargs:
            kwargs = {}
        else:
            self._check_valid_keys()

        if "concept_id" in kwargs:
            self._fmted_keys.update({"concept_id": kwargs["concept_id"]})

        if self.partype == "required":
            if not self._reqtype:
                raise TypeGuardException

            if self.check_req_values() and kwargs == {}:
                pass
            else:
                reqkeys = self.poss_keys[self._reqtype]
                defaults = {
                    "page_size": 2000,
                    "page_num": 0,
                    "request_mode": "async",
                    "include_meta": "Y",
                    "client_string": "icepyx",
                }

                for key in reqkeys:
                    if key == "short_name":
                        try:
                            self._fmted_keys.update({key: kwargs[key]})
                        except KeyError:
                            self._fmted_keys.update({key: kwargs["product"]})
                    elif key in kwargs:
                        self._fmted_keys.update({key: kwargs[key]})
                    elif key in defaults:
                        self._fmted_keys.update({key: defaults[key]})
                    else:
                        pass

        else:
            if self.check_values is True and kwargs is None:
                pass
            else:
                spatial_keys = self.poss_keys["spatial"]
                opt_keys = self.poss_keys["optional"]

                for key in opt_keys:
                    if key == "Coverage" and key in kwargs:
                        # DevGoal: make an option along the lines of Coverage=default,
                        # which will get the default variables for that product without
                        # the user having to input is2obj.build_wanted_wanted_var_list
                        # as their input value for using the Coverage kwarg
                        self._fmted_keys.update(
                            {key: _fmt_var_subset_list(kwargs[key])}
                        )
                    elif (key == "temporal" or key == "time") and (
                        "start" in kwargs and "end" in kwargs
                    ):
                        self._fmted_keys.update(
                            _fmt_temporal(kwargs["start"], kwargs["end"], key)
                        )
                    elif key in kwargs:
                        self._fmted_keys.update({key: kwargs[key]})
                    else:
                        pass

                if any(keys in self._fmted_keys for keys in spatial_keys):
                    pass
                else:
                    k = None
                    if self.partype == "CMR":
                        k = kwargs["extent_type"]
                    elif self.partype == "subset":
                        if kwargs["extent_type"] == "bounding_box":
                            k = "bbox"
                        elif kwargs["extent_type"] == "polygon":
                            k = "Boundingshape"

                    if not k:
                        raise TypeGuardException

                    self._fmted_keys.update({k: kwargs["spatial_extent"]})


CMRParameters = Parameters[Literal["CMR"]]
RequiredParameters = Parameters[Literal["required"]]
SubsetParameters = Parameters[Literal["subset"]]
