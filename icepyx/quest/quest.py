from icepyx.core.base_query import GenQuery
from icepyx.core.query import Query
from icepyx.quest.dataset_scripts.argo import Argo


class Quest(GenQuery):
    """
    QUEST - Query Unify Explore SpatioTemporal - object to query, obtain, and perform basic
    operations on datasets (i.e. Argo, BGC Argo, MODIS, etc) for combined analysis with ICESat-2
    data products. A new dataset can be added using the `dataset.py` template.
    QUEST expands the icepyx GenQuery superclass.

    See the doc page for GenQuery for details on temporal and spatial input parameters.

    Parameters
    ----------
    proj : proj4 string
        Geospatial projection.
        Not yet implemented

    Returns
    -------
    quest object

    Examples
    --------
    Initializing Quest with a bounding box.

    >>> reg_a_bbox = [-55, 68, -48, 71]
    >>> reg_a_dates = ['2019-02-20','2019-02-28']
    >>> reg_a = Quest(spatial_extent=reg_a_bbox, date_range=reg_a_dates)
    >>> print(reg_a)
    Extent type: bounding_box
    Coordinates: [-55.0, 68.0, -48.0, 71.0]
    Date range: (2019-02-20 00:00:00, 2019-02-28 23:59:59)
    Data sets: None

    Add datasets to the quest object.

    >>> reg_a.datasets = {'ATL07':None, 'Argo':None}
    >>> print(reg_a)
    Extent type: bounding_box
    Coordinates: [-55.0, 68.0, -48.0, 71.0]
    Date range: (2019-02-20 00:00:00, 2019-02-28 23:59:59)
    Data sets: ATL07, Argo

    See Also
    --------
    GenQuery
    """

    def __init__(
        self,
        spatial_extent,
        date_range,
        start_time=None,
        end_time=None,
        proj="default",
    ):
        """
        Tells QUEST to initialize data given the user input spatiotemporal data.
        """

        super().__init__(spatial_extent, date_range, start_time, end_time)
        self.datasets = {}

    def __str__(self):
        str = super(Quest, self).__str__()

        str += "\nData sets: "

        if not self.datasets:
            str += "None"
        else:
            for i in self.datasets:
                str += "{0}, ".format(i)
            str = str[:-2]  # remove last ', '

        return str

    # ----------------------------------------------------------------------
    # Datasets

    def add_icesat2(
        self,
        product,
        start_time=None,
        end_time=None,
        version=None,
        cycles=None,
        tracks=None,
        files=None,
        **kwargs,
    ) -> None:
        """
        Adds ICESat-2 datasets to QUEST structure.

        Parameters
        ----------
        For details on inputs, see the Query documentation.

        Returns
        -------
        None

        See Also
        --------
        icepyx.core.GenQuery
        icepyx.core.Query
        """

        query = Query(
            product,
            self._spatial.extent,
            [self._temporal.start, self._temporal.end],
            start_time,
            end_time,
            version,
            cycles,
            tracks,
            files,
            **kwargs,
        )

        self.datasets["icesat2"] = query

    def add_argo(self, params=["temperature"], presRange=None) -> None:
        """
        Adds Argo (including Argo-BGC) to QUEST structure.

        Parameters
        ----------
        For details on inputs, see the Argo dataset script documentation.

        Returns
        -------
        None

        See Also
        --------
        quest.dataset_scripts.argo
        icepyx.query.GenQuery

        Examples
        --------
        # example with profiles available
        >>> reg_a = Quest([-154, 30,-143, 37], ['2022-04-12', '2022-04-26'])
        >>> reg_a.add_argo(params=["temperature", "salinity"])
        """

        argo = Argo(self._spatial, self._temporal, params, presRange)
        self.datasets["argo"] = argo

    # ----------------------------------------------------------------------
    # Methods (on all datasets)

    # error handling? what happens when the user tries to re-query?
    def search_all(self, **kwargs):
        """
        Searches for required dataset within platform (i.e. ICESat-2, Argo) of interest.

        Parameters
        ----------
        **kwargs : default None
            Optional passing of keyword arguments to supply additional search constraints per datasets.
            Each key must match the dataset name (e.g. "icesat2", "argo") as in quest.datasets.keys(),
            and the value is a dictionary of acceptable keyword arguments
            and values allowable for the `search_data()` function for that dataset.
            For instance: `icesat2 = {"IDs":True}, argo = {"presRange":"10,500"}`.
        """
        print("\nSearching all datasets...")

        for k, v in self.datasets.items():
            print()
            try:
                if isinstance(v, Query):
                    print("---ICESat-2---")
                    try:
                        msg = v.avail_granules(kwargs[k])
                    except KeyError:
                        msg = v.avail_granules()
                    print(msg)
                else:
                    print(k)
                    try:
                        v.search_data(kwargs[k])
                    except KeyError:
                        v.search_data()

            except Exception:
                dataset_name = type(v).__name__
                print("Error querying data from {0}".format(dataset_name))

    # error handling? what happens if the user tries to re-download?
    def download_all(self, path="", **kwargs):
        """
        Downloads requested dataset(s).

        Parameters
        ----------
        **kwargs : default None
            Optional passing of keyword arguments to supply additional search constraints per datasets.
            Each key must match the dataset name (e.g. "icesat2", "argo") as in quest.datasets.keys(),
            and the value is a dictionary of acceptable keyword arguments
            and values allowable for the `search_data()` function for that dataset.
            For instance: `icesat2 = {"verbose":True}, argo = {"keep_existing":True}`.
        """

        print("\nDownloading all datasets...")

        for k, v in self.datasets.items():
            print()

            try:
                if isinstance(v, Query):
                    print("---ICESat-2---")
                    try:
                        msg = v.download_granules(path, kwargs[k])
                    except KeyError:
                        msg = v.download_granules(path)
                    print(msg)
                else:
                    print(k)
                    try:
                        msg = v.download(kwargs[k])
                    except KeyError:
                        msg = v.download()
                    print(msg)
            except Exception:
                dataset_name = type(v).__name__
                print("Error downloading data from {0}".format(dataset_name))

    def save_all(self, path):
        """
        Saves all datasets according to their respective `.save()` functionality.

        Parameters
        ----------
        path : str
            Path at which to save the dataset files.

        """

        for k, v in self.datasets.items():
            if isinstance(v, Query):
                print("ICESat-2 granules are saved during download")
            else:
                print("Saving " + k)
                v.save(path)
