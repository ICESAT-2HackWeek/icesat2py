import numpy as np
import datetime as dt
import re
import os
import getpass
import socket
import requests
import json
import warnings
import pprint
from xml.etree import ElementTree as ET
import time
import zipfile
import io
import math
import geopandas as gpd
from shapely.geometry import Polygon
import matplotlib.pyplot as plt

def validate_dataset(dataset):
    """
    Confirm a valid ICESat-2 dataset was specified
    """
    if isinstance(dataset, str):
        dataset = str.upper(dataset)
        assert dataset in ['ATL01','ATL02', 'ATL03', 'ATL04','ATL06', 'ATL07', 'ATL08', 'ATL09', 'ATL10', \
                           'ATL12', 'ATL13'],\
        "Please enter a valid dataset"
    else:
        raise TypeError("Please enter a dataset string")
    return dataset
#DevQuestion: since this function is validating an entry, does it also make sense to have a test for it?
#DevGoal: See if there's a way to dynamically get this list so it's automatically updated


class Icesat2Data():
    """
    ICESat-2 Data object to query, obtain, and perform basic operations on
    available ICESat-2 datasets using temporal and spatial input parameters.
    Allows the easy input and formatting of search parameters to match the
    NASA NSIDC DAAC and conversion to multiple data types.

    Parameters
    ----------
    dataset : string
        ICESat-2 dataset ID, also known as "short name" (e.g. ATL03).
        Available datasets can be found at: https://nsidc.org/data/icesat-2/data-sets
    spatial_extent : list
        Spatial extent of interest, provided as a bounding box.
        Bounding box coordinates should be provided in decimal degrees as
        [lower-left-longitude, lower-left-latitute, upper-right-longitude, upper-right-latitude].
        DevGoal: allow broader input of polygons and polygon files (e.g. kml, shp) as bounding areas
    date_range : list of 'YYYY-MM-DD' strings
        Date range of interest, provided as start and end dates, inclusive.
        The required date format is 'YYYY-MM-DD' strings, where
        YYYY = 4 digit year, MM = 2 digit month, DD = 2 digit day.
        Currently, a list of specific dates (rather than a range) is not accepted.
        DevGoal: accept date-time objects, dicts (with 'start_date' and 'end_date' keys, and DOY inputs).
        DevGoal: allow searches with a list of dates, rather than a range.
    start_time : HH:mm:ss, default 00:00:00
        Start time in UTC/Zulu (24 hour clock). If None, use default.
        DevGoal: check for time in date-range date-time object, if that's used for input.
    end_time : HH:mm:ss, default 23:59:59
        End time in UTC/Zulu (24 hour clock). If None, use default.
        DevGoal: check for time in date-range date-time object, if that's used for input.
    version : string, default most recent version
        Dataset version, given as a 3 digit string. If no version is given, the current
        version is used.


    See Also
    --------


    Examples
    --------
    Initializing Icesat2Data with a bounding box.
    >>> reg_a_bbox = [-64, 66, -55, 72]
    >>> reg_a_dates = ['2019-02-22','2019-02-28']
    >>> region_a = icepyx.Icesat2Data('ATL06', reg_a_bbox, reg_a_dates)
    >>> region_a
    [show output here after inputting above info and running it]
    """

    # ----------------------------------------------------------------------
    # Constructors

    def __init__(
        self,
        dataset = None,
        spatial_extent = None,
        date_range = None,
        start_time = None,
        end_time = None,
        version = None,
    ):

        if dataset is None or spatial_extent is None or date_range is None:
            raise ValueError("Please provide the required inputs. Use help([function]) to view the function's documentation")


        self._dset = validate_dataset(dataset)

        if isinstance(spatial_extent, list):
            if len(spatial_extent)==4:
                #BestPractices: move these assertions to a more general set of tests for valid geometries?
                assert -90 <= spatial_extent[1] <= 90, "Invalid latitude value"
                assert -90 <= spatial_extent[3] <= 90, "Invalid latitude value"
                assert -180 <= spatial_extent[0] <= 360, "Invalid longitude value" #tighten these ranges depending on actual allowed inputs
                assert -180 <= spatial_extent[2] <= 360, "Invalid longitude value"
                assert spatial_extent[0] <= spatial_extent[2], "Invalid bounding box longitudes"
                assert spatial_extent[1] <= spatial_extent[3], "Invalid bounding box latitudes"
                self._spat_extent = spatial_extent
                self.extent_type = 'bounding_box'
            else:
                assert spatial_extent[0] == spatial_extent[-2], "Starting longitude doesn't match ending longitude"
                assert spatial_extent[1] == spatial_extent[-1], "Starting latitude doesn't match ending latitude"
                self._spat_extent = spatial_extent
                self.extent_type = 'polygon'
                # raise ValueError('Your spatial extent bounding box needs to have four entries')
        elif isinstance(spatial_extent, str):
            if spatial_extent.split('.')[-1] == 'kml' or spatial_extent.split('.')[-1] == 'shp' or spatial_extent.split('.')[-1] == 'gpkg':
                #polygon formatting code borrowed from Amy Steiker's 03_NSIDCDataAccess_Steiker.ipynb demo.
                gdf = gpd.read_file(spatial_extent)
                poly = gdf.iloc[0].geometry
                # # Simplify polygon. The larger the tolerance value, the more simplified the polygon.
                # poly = poly.simplify(0.05, preserve_topology=False)
                # #Format dictionary to polygon coordinate pairs for CMR polygon filtering
                polygon = ','.join([str(c) for xy in zip(*poly.exterior.coords.xy) for c in xy])
                self._spat_extent = polygon
                self.extent_type = 'polygon'
            else:
                print('spatial file extent does not appear to be either kml,shp or gpkg')

        if isinstance(date_range, list):
            if len(date_range)==2:
                self._start = dt.datetime.strptime(date_range[0], '%Y-%m-%d')
                self._end = dt.datetime.strptime(date_range[1], '%Y-%m-%d')
                #BestPractices: can the check that it's a valid date entry be implicit (e.g. by converting it to a datetime object, as done here?) or must it be more explicit?
                assert self._start.date() <= self._end.date(), "Your date range is invalid"
            else:
                raise ValueError("Your date range list is the wrong length. It should have start and end dates only.")

#         elif isinstance(date_range, date-time object):
#             print('it is a date-time object')
#         elif isinstance(date_range, dict):
#             print('it is a dictionary. now check the keys for start and end dates')


        if start_time is None:
            self._start = self._start.combine(self._start.date(),dt.datetime.strptime('00:00:00', '%H:%M:%S').time())
        else:
            if isinstance(start_time, str):
                self._start = self._start.combine(self._start.date(),dt.datetime.strptime(start_time, '%H:%M:%S').time())
            else:
                raise TypeError("Please enter your start time as a string")

        if end_time is None:
            self._end = self._start.combine(self._end.date(),dt.datetime.strptime('23:59:59', '%H:%M:%S').time())
        else:
            if isinstance(end_time, str):
                self._end = self._start.combine(self._end.date(),dt.datetime.strptime(end_time, '%H:%M:%S').time())
            else:
                raise TypeError("Please enter your end time as a string")

        latest_vers = self.latest_version()
        if version is None:
            self._version = latest_vers
        else:
            if isinstance(version, str):
                assert int(version)>0, "Version number must be positive"
                vers_length = 3
                self._version = version.zfill(vers_length)
            else:
                raise TypeError("Please enter the version number as a string")

            if int(self._version) < int(latest_vers):
                warnings.filterwarnings("always")
                warnings.warn("You are using an old version of this dataset")


    # ----------------------------------------------------------------------
    # Properties

    @property
    def dataset(self):
        """
        Return the short name dataset ID string associated with the ICESat-2 data object.

        Example
        --------
        >>> region_a = icepyx.Icesat2Data('ATL06',[-64, 66, -55, 72],['2019-02-22','2019-02-28'])
        >>> region_a.dataset
        ATL06
        """
        return self._dset

    @property
    def spatial_extent(self):
        """
        Return an array showing the spatial extent of the ICESat-2 data object.
        Spatial extent is returned as an input type followed by the geometry data.
        Bounding box data is [lower-left-longitude, lower-left-latitute, upper-right-longitude, upper-right-latitude].

        Examples
        --------
        >>> region_a = icepyx.Icesat2Data('ATL06',[-64, 66, -55, 72],['2019-02-22','2019-02-28'])
        >>> region_a.spatial_extent
        ['bounding box', [-64, 66, -55, 72]]
        """

        if self.extent_type is 'bounding_box':
            return ['bounding box', self._spat_extent]
        elif self.extent_type is 'polygon':
            return ['polygon', self._spat_extent]
        else:
            return ['unknown spatial type', self._spat_extent]

    @property
    def geodataframe(self):
        """
        Return a geodataframe of the spatial extent


        Examples
        --------
        >>> region_a = icepyx.Icesat2Data('ATL06','path/spatialfile.shp',['2019-02-22','2019-02-28'])
        >>> gdf = region_a.geodataframe
        """

        if self.extent_type is 'bounding_box':
            gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(self._spat_extent[0::2], self._spat_extent[1::2]))
            return gdf
        if self.extent_type is 'polygon':
            spat_extent = self._spat_extent
            if isinstance(spat_extent,str):
                spat_extent = spat_extent.split(',')
            spat_extent_list = [float(val) for val in spat_extent]
            spatial_extent_geom = Polygon(zip(spat_extent_list[0::2], spat_extent_list[1::2]))
            gdf = gpd.GeoDataFrame(index=[0],crs={'init':'epsg:4326'}, geometry=[spatial_extent_geom])
            return gdf
        else:
            return ['unknown spatial type', self._spat_extent]

    @property
    def vizualize_spatial_extent(self): #additional args, basemap, zoom level, cmap, export
        """
        Creates a map of the inputted spatial extent


        Examples
        --------
        >>> icepyx.Icesat2Data('ATL06','path/spatialfile.shp',['2019-02-22','2019-02-28'])
        >>> region_a.vizualize_spatial_extent
        """

        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        f, ax = plt.subplots(1, figsize=(12, 6))
        world.plot(ax=ax, facecolor='lightgray', edgecolor='gray')
        self.geodataframe.plot(ax=ax, color='#FF8C00',alpha = '0.7')

        plt.show()


    @property
    def dates(self):
        """
        Return an array showing the date range of the ICESat-2 data object.
        Dates are returned as an array containing the start and end datetime objects, inclusive, in that order.

        Examples
        --------
        >>> region_a = icepyx.Icesat2Data('ATL06',[-64, 66, -55, 72],['2019-02-22','2019-02-28'])
        >>> region_a.dates
        ['2019-02-22', '2019-02-28']
        """
        return [self._start.strftime('%Y-%m-%d'), self._end.strftime('%Y-%m-%d')] #could also use self._start.date()


    @property
    def start_time(self):
        """
        Return the start time specified for the start date.

        Examples
        --------
        >>> region_a = icepyx.Icesat2Data('ATL06',[-64, 66, -55, 72],['2019-02-22','2019-02-28'])
        >>> region_a.start_time
        00:00:00

        >>> region_a = icepyx.Icesat2Data('ATL06',[-64, 66, -55, 72],['2019-02-22','2019-02-28'], start_time='12:30:30')
        >>> region_a.start_time
        12:30:30
        """
        return self._start.strftime('%H:%M:%S')

    @property
    def end_time(self):
        """
        Return the end time specified for the end date.

        Example
        --------
        >>> region_a = icepyx.Icesat2Data('ATL06',[-64, 66, -55, 72],['2019-02-22','2019-02-28'])
        >>> region_a.end_time
        23:59:59

        >>> region_a = icepyx.Icesat2Data('ATL06',[-64, 66, -55, 72],['2019-02-22','2019-02-28'], end_time='10:20:20')
        >>> region_a.end_time
        10:20:20
        """
        return self._end.strftime('%H:%M:%S')

    @property
    def dataset_version(self):
        """
        Return the dataset version of the data object.

        Example
        --------
        >>> region_a = icepyx.Icesat2Data('ATL06',[-64, 66, -55, 72],['2019-02-22','2019-02-28'])
        >>> region_a.dataset_version
        002

        >>> region_a = icepyx.Icesat2Data('ATL06',[-64, 66, -55, 72],['2019-02-22','2019-02-28'], version='1')
        >>> region_a.dataset_version
        001
        """
        return self._version

    #Note: Would it be helpful to also have start and end properties that give the start/end date+time?

    @property
    def granule_info(self):
        """
        Return some basic information about the granules available for the given ICESat-2 data object.

        Example
        --------
        >>>
        """
        gran_info = {}
        gran_info.update({'Number of available granules': len(self.granules)})

        gran_sizes = [float(gran['granule_size']) for gran in self.granules]
        gran_info.update({'Average size of granules (MB)': np.mean(gran_sizes)})
        gran_info.update({'Total size of all granules (MB)': sum(gran_sizes)})

        return gran_info


    # ----------------------------------------------------------------------
    # Static Methods

    @staticmethod
    def cmr_fmt_temporal(start,end,key): #make this more general in name b/c can be used to format for CMR or subset spatial
        """
        Format the start and end dates and times into a temporal CMR search key.

        Parameters
        ----------
        start : date time object
            Start date and time for the period of interest.
        end : date time object
            End date and time for the period of interest.
        key : string
            Dictionary key, entered as a string, indicating which temporal format is needed.
            Must be one of ['temporal','time']
        """

        assert isinstance(start, dt.datetime)
        assert isinstance(end, dt.datetime)
        #DevGoal: add test for proper keys
        if key is 'temporal':
            fmt_timerange = start.strftime('%Y-%m-%dT%H:%M:%SZ') +',' + end.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif key is 'time':
            fmt_timerange = start.strftime('%Y-%m-%dT%H:%M:%S') +',' + end.strftime('%Y-%m-%dT%H:%M:%S')

        return {key:fmt_timerange}

    @staticmethod
    def cmr_fmt_spatial(ext_type,extent): #make this more general in name b/c can be used to format for CMR or subset spatial
        """
        Format the spatial extent input into a spatial CMR search key.

        Parameters
        ----------
        extent_type : string
            Spatial extent type. Must be one of ['bounding_box'].
        extent : list
            Spatial extent, with input format dependent on the extent type.
            Bounding box coordinates should be provided in decimal degrees as
            [lower-left-longitude, lower-left-latitute, upper-right-longitude, upper-right-latitude].
        """

        assert ext_type in ['bounding_box', 'bbox','polygon','bounding_shape'], "Invalid spatial extent type."

        if ext_type in ['bounding_box', 'bbox','polygon','bounding_shape']:
            fmt_extent = ','.join(map(str, extent))

        return {ext_type: fmt_extent}

    @staticmethod
    def combine_params(*param_dicts):
        params={}
        for dictionary in param_dicts:
            params.update(dictionary)
        return params



    # ----------------------------------------------------------------------
    # Methods

    def about_dataset(self):
        """
        Return metadata about the dataset of interest (the collection).
        """

        cmr_collections_url = 'https://cmr.earthdata.nasa.gov/search/collections.json'
        response = requests.get(cmr_collections_url, params={'short_name': self._dset})
        results = json.loads(response.content)
        return results
        #DevGoal: provide a more readable data format if the user prints the data (look into pprint, per Amy's tutorial)


    def latest_version(self):
        """
        Determine the most recent version available for the given dataset.
        """
        dset_info = self.about_dataset()
        return max([entry['version_id'] for entry in dset_info['feed']['entry']])

    def get_custom_options(self, session):
        capability_url = f'https://n5eil02u.ecs.nsidc.org/egi/capabilities/{self.dataset}.{self._version}.xml'
        response = session.get(capability_url)
        root = ET.fromstring(response.content)

        # collect lists with each service option
        subagent = [subset_agent.attrib for subset_agent in root.iter('SubsetAgent')]

        # variable subsetting
        variables = [SubsetVariable.attrib for SubsetVariable in root.iter('SubsetVariable')]
        variables_raw = [variables[i]['value'] for i in range(len(variables))]
        variables_join = [''.join(('/',v)) if v.startswith('/') == False else v for v in variables_raw]
        variable_vals = [v.replace(':', '/') for v in variables_join]

        # reformatting
        formats = [Format.attrib for Format in root.iter('Format')]
        format_vals = [formats[i]['value'] for i in range(len(formats))]
        format_vals.remove('')

        # reprojection only applicable on ICESat-2 L3B products, yet to be available.

        # reformatting options that support reprojection
        normalproj = [Projections.attrib for Projections in root.iter('Projections')]
        normalproj_vals = []
        normalproj_vals.append(normalproj[0]['normalProj'])
        format_proj = normalproj_vals[0].split(',')
        format_proj.remove('')
        format_proj.append('No reformatting')

        #reprojection options
        projections = [Projection.attrib for Projection in root.iter('Projection')]
        proj_vals = []
        for i in range(len(projections)):
            if (projections[i]['value']) != 'NO_CHANGE' :
                proj_vals.append(projections[i]['value'])

        # reformatting options that do not support reprojection
        no_proj = [i for i in format_vals if i not in format_proj]

        print(subagent, variable_vals, format_vals, normalproj_vals, proj_vals, no_proj)

    def build_CMR_params(self):
        """
        Build a dictionary of CMR parameter keys to submit for granule searches and download.
        """

        if not hasattr(self,'CMRparams'):
            self.CMRparams={}

        CMR_solo_keys = ['short_name','version','temporal']
        CMR_spat_keys = ['bounding_box','polygon']
        #check to see if the parameter list is already built
        if all(keys in self.CMRparams for keys in CMR_solo_keys) and any(keys in self.CMRparams for keys in CMR_spat_keys):
            pass
        #if not, see which fields need to be added and add them
        else:
            for key in CMR_solo_keys:
                if key in self.CMRparams:
                    pass
                else:
                    if key is 'short_name':
                        self.CMRparams.update({key:self.dataset})
                    elif key is 'version':
                        self.CMRparams.update({key:self._version})
                    elif key is 'temporal':
                        self.CMRparams.update(self.cmr_fmt_temporal(self._start,self._end,key))
            if any(keys in self.CMRparams for keys in CMR_spat_keys):
                pass
            else:
                self.CMRparams.update(self.cmr_fmt_spatial(self.extent_type,self._spat_extent))

    def build_subset_params(self, **kwargs):
        """
        Build a dictionary of subsetting parameter keys to submit for data orders and download.
        """

        if not hasattr(self,'subsetparams'):
            self.subsetparams={}

        default_keys = ['time']
        spat_keys = ['bbox','bounding_shape']
        opt_keys = ['format','projection','projection_parameters','Coverage']
        #check to see if the parameter list is already built
        if all(keys in self.subsetparams for keys in default_keys) and any(keys in self.subsetparams for keys in spat_keys):
            pass
        #if not, see which fields need to be added and add them
        else:
            for key in default_keys:
                if key in self.subsetparams:
                    pass
                else:
                    if key is 'time':
                        self.subsetparams.update(self.cmr_fmt_temporal(self._start,self._end, key))
            if any(keys in self.subsetparams for keys in spat_keys):
                pass
            else:
                if self.extent_type is 'bounding_box':
                    k = 'bbox'
                elif self.extent_type is 'polygon':
                    k = 'bounding_shape'
                self.subsetparams.update(self.cmr_fmt_spatial(k,self._spat_extent))
            for key in opt_keys:
                if key in kwargs:
                    self.subsetparams.update({key:kwargs[key]})
                else:
                    pass




    def build_reqconfig_params(self,reqtype, **kwargs):
        """
        Build a dictionary of request configuration parameters.
        #DevGoal: Allow updating of the request configuration parameters (right now they must be manually deleted to be modified)
        """

        if not hasattr(self,'reqparams'):
            self.reqparams={}

        if reqtype is 'search':
            reqkeys = ['page_size','page_num']
        elif reqtype is 'download':
            reqkeys = ['page_size','page_num','request_mode','token','email','include_meta']
        else:
            raise ValueError("Invalid request type")

        if all(keys in self.reqparams for keys in reqkeys):
            pass
        else:
            defaults={'page_size':10,'page_num':1,'request_mode':'async','include_meta':'Y'}
            for key in reqkeys:
                if key in kwargs:
                    self.reqparams.update({key:kwargs[key]})
#                 elif key in defaults:
#                     if key is 'page_num':
#                         pnum = math.ceil(len(self.granules)/self.reqparams['page_size'])
#                         if pnum > 0:
#                             self.reqparams.update({key:pnum})
#                         else:
#                             self.reqparams.update({key:defaults[key]})
                elif key in defaults:
                    self.reqparams.update({key:defaults[key]})
                else:
                    pass


    def avail_granules(self):
        """
        Get a list of available granules for the ICESat-2 data object's parameters
        """

        granule_search_url = 'https://cmr.earthdata.nasa.gov/search/granules'

        self.granules = []
        self.build_CMR_params()
        self.build_reqconfig_params('search')
        headers={'Accept': 'application/json'}
        while True:
            response = requests.get(granule_search_url, headers=headers,\
                                    params=self.combine_params(self.CMRparams,\
                                                               {k: self.reqparams[k] for k in ('page_size','page_num')}))
            results = json.loads(response.content)

            #DevGoal: check that there ARE results (ie not an empty search) and let the user know if that's the case
            if len(results['feed']['entry']) == 0:
                # Out of results, so break out of loop
                break

            # Collect results and increment page_num
            self.granules.extend(results['feed']['entry'])
            self.reqparams['page_num'] += 1

        return self.granule_info


    def earthdata_login(self,uid,email):
        """
        Initiate an Earthdata session and create a token for interacting
        with the NSIDC DAAC. This function will prompt the user for
        their Earthdata password, but will only store that information
        within the active session.

        Parameters
        ----------
        uid : string
            Earthdata Login user name.
        email : string
            Complete email address, provided as a string.

        Example
        --------
        >>> region_a = [define that here]
        >>> region_a.earthdata_login('sam.smith','sam.smith@domain.com')
        Earthdata Login password:  ········
        """

        if not hasattr(self,'reqparams'):
            self.reqparams={}

        assert isinstance(uid, str), "Enter your login user id as a string"
        assert re.match(r'[^@]+@[^@]+\.[^@]+',email), "Enter a properly formatted email address"

        pswd = getpass.getpass('Earthdata Login password: ')

        #Request CMR token using Earthdata credentials
        token_api_url = 'https://cmr.earthdata.nasa.gov/legacy-services/rest/tokens'
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)

        data = {'token': {'username': uid, 'password': pswd,\
                          'client_id': 'NSIDC_client_id','user_ip_address': ip}
        }
        response = requests.post(token_api_url, json=data, headers={'Accept': 'application/json'})
        token = json.loads(response.content)['token']['id']

        self.reqparams.update({'email': email, 'token': token})

        #Start a session
        capability_url = f'https://n5eil02u.ecs.nsidc.org/egi/capabilities/{self.dataset}.{self._version}.xml'
        session = requests.session()
        s = session.get(capability_url)
        response = session.get(s.url,auth=(uid,pswd))

        return session


    def order_granules(self, session, verbose=False, subset=True, **kwargs):
        """
        Place an order for the available granules for the ICESat-2 data object.
        Adds the list of zipped files (orders) to the data object.
        DevGoal: add additional kwargs to allow subsetting and more control over request options.
        Note: This currently uses paging to download data - this may not be the best method

        Parameters
        ----------
        session : requests.session object
            A session object authenticating the user to download data using their Earthdata login information.
            The session object can be obtained using is2_data.earthdata_login(uid, email) and entering your
            Earthdata login password when prompted. You must have previously registered for an Earthdata account.

        verbose : boolean, default False
            Print out all feedback available from the order process.
            Progress information is automatically printed regardless of the value of verbose.

        subset : boolean, default True
            Use input temporal and spatial search parameters to subset each granule and return only data
            that is actually within those parameters (rather than complete granules which may contain only
            a small area of interest).

        kwargs...
        """

        if session is None:
            raise ValueError("Don't forget to log in to Earthdata using is2_data.earthdata_login(uid, email)")
            #DevGoal: make this a more robust check for an active session

        base_url = 'https://n5eil02u.ecs.nsidc.org/egi/request'
        #DevGoal: get the base_url from the granules

        self.build_CMR_params()
        self.build_reqconfig_params('download')

        if subset is False:
            request_params = self.combine_params(self.CMRparams, self.reqparams, {'agent':'NO'})
        else:
#             if kwargs is None:
#                 #make subset params and add them to request params
#                 self.build_subset_params()
#                 request_params = self.combine_params(self.CMRparams, self.reqparams, self.subsetparams)
#             else:
#                 #make subset params using kwargs and add them to request params
#                 self.build_subset_params(kwargs)
#                 request_params = self.combine_params(self.CMRparams, self.reqparams, self.subsetparams)
            self.build_subset_params(**kwargs)
            request_params = self.combine_params(self.CMRparams, self.reqparams, self.subsetparams)


        granules=self.avail_granules() #this way the reqparams['page_num'] is updated

        # Request data service for each page number, and unzip outputs
        for i in range(request_params['page_num']):
            page_val = i + 1
            if verbose is True:
                print('Order: ', page_val)
            request_params.update( {'page_num': page_val} )

        # For all requests other than spatial file upload, use get function
            request = session.get(base_url, params=request_params)

            if verbose is True:
                print('Request HTTP response: ', request.status_code)

        # Raise bad request: Loop will stop for bad response code.
            request.raise_for_status()
            esir_root = ET.fromstring(request.content)
            if verbose is True:
                print('Order request URL: ', request.url)
                print('Order request response XML content: ', request.content)

        #Look up order ID
            orderlist = []
            for order in esir_root.findall("./order/"):
                if verbose is True:
                    print(order)
                orderlist.append(order.text)
            orderID = orderlist[0]
            print('order ID: ', orderID)

        #Create status URL
            statusURL = base_url + '/' + orderID
            if verbose is True:
                print('status URL: ', statusURL)

        #Find order status
            request_response = session.get(statusURL)
            if verbose is True:
                print('HTTP response from order response URL: ', request_response.status_code)

        # Raise bad request: Loop will stop for bad response code.
            request_response.raise_for_status()
            request_root = ET.fromstring(request_response.content)
            statuslist = []
            for status in request_root.findall("./requestStatus/"):
                statuslist.append(status.text)
            status = statuslist[0]
            print('Data request ', page_val, ' is submitting...')
            print('Initial request status is ', status)

        #Continue loop while request is still processing
            while status == 'pending' or status == 'processing':
                print('Status is not complete. Trying again.')
                time.sleep(10)
                loop_response = session.get(statusURL)

        # Raise bad request: Loop will stop for bad response code.
                loop_response.raise_for_status()
                loop_root = ET.fromstring(loop_response.content)

        #find status
                statuslist = []
                for status in loop_root.findall("./requestStatus/"):
                    statuslist.append(status.text)
                status = statuslist[0]
                print('Retry request status is: ', status)
                if status == 'pending' or status == 'processing':
                    continue

        #Order can either complete, complete_with_errors, or fail:
        # Provide complete_with_errors error message:
            if status == 'complete_with_errors' or status == 'failed':
                messagelist = []
                for message in loop_root.findall("./processInfo/"):
                    messagelist.append(message.text)
                print('error messages:')
                pprint.pprint(messagelist)

            if status == 'complete' or status == 'complete_with_errors':
                if not hasattr(self,'orderIDs'):
                    self.orderIDs=[]

                self.orderIDs.append(orderID)
            else: print('Request failed.')



    def download_granules(self, session, path, verbose=False): #, extract=False):
        """
        Downloads the data ordered using order_granules.

        Parameters
        ----------
        session : requests.session object
            A session object authenticating the user to download data using their Earthdata login information.
            The session object can be obtained using is2_data.earthdata_login(uid, email) and entering your
            Earthdata login password when prompted. You must have previously registered for an Earthdata account.
        path : string
            String with complete path to desired download location.
        verbose : boolean, default False
            Print out all feedback available from the download process.
            Progress information is automatically printed regardless of the value of verbose.
        """
        """
        extract : boolean, default False
            Unzip the downloaded granules.
        """

        #Note: need to test these checks still
        if session is None:
            raise ValueError("Don't forget to log in to Earthdata using is2_data.earthdata_login(uid, email)")
            #DevGoal: make this a more robust check for an active session

        if not hasattr(self,'orderIDs') or len(self.orderIDs)==0:
            try:
                self.order_granules(session, verbose=verbose)
            except:
                if not hasattr(self,'orderIDs') or len(self.orderIDs)==0:
                    raise ValueError('Please confirm that you have submitted a valid order and it has successfully completed.')

        if not os.path.exists(path):
            os.mkdir(path)

        os.chdir(path)

        for order in self.orderIDs:
            downloadURL = 'https://n5eil02u.ecs.nsidc.org/esir/' + order + '.zip'
            #DevGoal: get the download_url from the granules

            if verbose is True:
                print('Zip download URL: ', downloadURL)
            print('Beginning download of zipped output...')
            zip_response = session.get(downloadURL)
            # Raise bad request: Loop will stop for bad response code.
            zip_response.raise_for_status()
            print('Data request', order, 'of ', len(self.orderIDs), ' order(s) is complete.')

#         #Note: extract the dataset to save it locally
#         if extract is True:
            with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
                z.extractall(path)
