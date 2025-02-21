import re

import pytest
import responses

import icepyx as ipx
from icepyx.core import granules as granules
from icepyx.core.exceptions import NsidcQueryError
from icepyx.core.granules import Granules as Granules

# @pytest.fixture
# def reg_a():
#     return ipx.Query('ATL06',[-55, 68, -48, 71],['2019-02-22','2019-02-28'])

# #@patch('my_module.__get_input', return_value='y')

# check that agent key is added in event of no subsetting


# add test for granules info for ATL11 and ATL13
# (and all datasets? or at least ones that don't have the same filename structure)
# this example failed in version 0.6.4,  leading to a fix in 0.6.5
# short_name = 'ATL11'
# spatial_extent = [-38.65,72.5,-38.40,72.7]
# date_range = ['2018-06-20','2023-01-21']
# region_a = ipx.Query(short_name, spatial_extent, date_range)
# region_a.avail_granules(ids=True)

# add test that s3urls are gotten for ALL products (e.g. ATL15 was failing
# due to .nc extension instead of .h5))


# DevNote: clearly there's a better way that doesn't make the function so long...
# what is it?
def test_granules_info():
    # reg_a = ipx.Query('ATL06', [-55, 68, -48, 71], ['2019-02-20','2019-02-24'], version='3')
    # granules = reg_a.granules.avail
    grans = [
        {
            "producer_granule_id": "ATL06_20190221121851_08410203_003_01.h5",
            "time_start": "2019-02-21T12:19:05.000Z",
            "orbit": {
                "ascending_crossing": "-40.35812957405553",
                "start_lat": "59.5",
                "start_direction": "A",
                "end_lat": "80",
                "end_direction": "A",
            },
            "updated": "2020-05-04T15:43:02.942Z",
            "orbit_calculated_spatial_domains": [
                {
                    "equator_crossing_date_time": "2019-02-21T12:03:18.922Z",
                    "equator_crossing_longitude": "-40.35812957405553",
                    "orbit_number": "2429",
                }
            ],
            "dataset_id": "ATLAS/ICESat-2 L3A Land Ice Height V003",
            "data_center": "NSIDC_ECS",
            "title": "SC:ATL06.003:177534295",
            "coordinate_system": "ORBIT",
            "time_end": "2019-02-21T12:24:16.000Z",
            "id": "G1723268629-NSIDC_ECS",
            "original_format": "ISO-SMAP",
            "granule_size": "50.3300800323",
            "browse_flag": True,
            "polygons": [
                [
                    "60.188087866839815 -48.12471565111877 79.13565976324539 -56.91308349854652 79.82054625244331 -57.75066986682175 79.88471463831527 -55.94835931630358 79.19580392788636 -55.21962622534677 60.21083561664105 -47.47451382423887 60.188087866839815 -48.12471565111877"
                ]
            ],
            "collection_concept_id": "C1706333750-NSIDC_ECS",
            "online_access_flag": True,
            "links": [
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                    "type": "application/x-hdfeos",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP7/ATLAS/ATL06.003/2019.02.21/ATL06_20190221121851_08410203_003_01.h5",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.default.default1.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.default.default2.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt1l.atl06_quality_summary.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt1l.h_li.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt1l.h_li_sigma.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt1l.n_fit_photons.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt1l.signal_selection_source.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt1r.atl06_quality_summary.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt1r.h_li.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt1r.h_li_sigma.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt1r.n_fit_photons.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt1r.signal_selection_source.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt2l.atl06_quality_summary.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt2l.h_li.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt2l.h_li_sigma.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt2l.n_fit_photons.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt2l.signal_selection_source.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt2r.atl06_quality_summary.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt2r.h_li.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt2r.h_li_sigma.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt2r.n_fit_photons.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt2r.signal_selection_source.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt3l.atl06_quality_summary.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt3l.h_li.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt3l.h_li_sigma.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt3l.n_fit_photons.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt3l.signal_selection_source.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt3r.atl06_quality_summary.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt3r.h_li.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt3r.h_li_sigma.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt3r.n_fit_photons.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.16/ATL06_20190221121851_08410203_003_01_BRW.gt3r.signal_selection_source.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                    "type": "text/xml",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP7/ATLAS/ATL06.003/2019.02.21/ATL06_20190221121851_08410203_003_01.iso.xml",
                },
                {
                    "inherited": True,
                    "length": "0.0KB",
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/ATLAS/ATL06.003/",
                },
                {
                    "inherited": True,
                    "length": "0.0KB",
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                    "hreflang": "en-US",
                    "href": "https://search.earthdata.nasa.gov/search/granules?p=C1706333750-NSIDC_ECS&q=atl06%20v003&m=-29.109278436791882!-59.86889648437499!1!1!0!0%2C2&tl=1572814258!4!!",
                },
                {
                    "inherited": True,
                    "length": "0.0KB",
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                    "hreflang": "en-US",
                    "href": "https://openaltimetry.org/",
                },
                {
                    "inherited": True,
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                    "hreflang": "en-US",
                    "href": "https://doi.org/10.5067/ATLAS/ATL06.003",
                },
                {
                    "inherited": True,
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                    "hreflang": "en-US",
                    "href": "https://doi.org/10.5067/ATLAS/ATL06.003",
                },
            ],
        },
        {
            "producer_granule_id": "ATL06_20190222010344_08490205_003_01.h5",
            "time_start": "2019-02-22T01:03:44.000Z",
            "orbit": {
                "ascending_crossing": "130.68730694092687",
                "start_lat": "80",
                "start_direction": "D",
                "end_lat": "59.5",
                "end_direction": "D",
            },
            "updated": "2020-05-04T15:35:15.570Z",
            "orbit_calculated_spatial_domains": [
                {
                    "equator_crossing_date_time": "2019-02-22T00:37:38.252Z",
                    "equator_crossing_longitude": "130.68730694092687",
                    "orbit_number": "2437",
                }
            ],
            "dataset_id": "ATLAS/ICESat-2 L3A Land Ice Height V003",
            "data_center": "NSIDC_ECS",
            "title": "SC:ATL06.003:177974050",
            "coordinate_system": "ORBIT",
            "time_end": "2019-02-22T01:07:47.000Z",
            "id": "G1725880106-NSIDC_ECS",
            "original_format": "ISO-SMAP",
            "granule_size": "42.656709671",
            "browse_flag": True,
            "polygons": [
                [
                    "80.11254119920325 -43.315444387475495 64.79892188605879 -52.21277462684438 64.82548575330607 -52.971370058601465 80.17859740110205 -45.168520453661074 80.11254119920325 -43.315444387475495"
                ]
            ],
            "collection_concept_id": "C1706333750-NSIDC_ECS",
            "online_access_flag": True,
            "links": [
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                    "type": "application/x-hdfeos",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP7/ATLAS/ATL06.003/2019.02.22/ATL06_20190222010344_08490205_003_01.h5",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.default.default1.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.default.default2.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt1l.atl06_quality_summary.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt1l.h_li.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt1l.h_li_sigma.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt1l.n_fit_photons.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt1l.signal_selection_source.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt1r.atl06_quality_summary.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt1r.h_li.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt1r.h_li_sigma.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt1r.n_fit_photons.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt1r.signal_selection_source.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt2l.atl06_quality_summary.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt2l.h_li.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt2l.h_li_sigma.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt2l.n_fit_photons.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt2l.signal_selection_source.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt2r.atl06_quality_summary.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt2r.h_li.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt2r.h_li_sigma.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt2r.n_fit_photons.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt2r.signal_selection_source.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt3l.atl06_quality_summary.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt3l.h_li.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt3l.h_li_sigma.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt3l.n_fit_photons.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt3l.signal_selection_source.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt3r.atl06_quality_summary.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt3r.h_li.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt3r.h_li_sigma.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt3r.n_fit_photons.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                    "type": "image/jpeg",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP0/BRWS/Browse.001/2020.04.22/ATL06_20190222010344_08490205_003_01_BRW.gt3r.signal_selection_source.jpg",
                },
                {
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                    "type": "text/xml",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/DP7/ATLAS/ATL06.003/2019.02.22/ATL06_20190222010344_08490205_003_01.iso.xml",
                },
                {
                    "inherited": True,
                    "length": "0.0KB",
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                    "hreflang": "en-US",
                    "href": "https://n5eil01u.ecs.nsidc.org/ATLAS/ATL06.003/",
                },
                {
                    "inherited": True,
                    "length": "0.0KB",
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                    "hreflang": "en-US",
                    "href": "https://search.earthdata.nasa.gov/search/granules?p=C1706333750-NSIDC_ECS&q=atl06%20v003&m=-29.109278436791882!-59.86889648437499!1!1!0!0%2C2&tl=1572814258!4!!",
                },
                {
                    "inherited": True,
                    "length": "0.0KB",
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                    "hreflang": "en-US",
                    "href": "https://openaltimetry.org/",
                },
                {
                    "inherited": True,
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                    "hreflang": "en-US",
                    "href": "https://doi.org/10.5067/ATLAS/ATL06.003",
                },
                {
                    "inherited": True,
                    "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                    "hreflang": "en-US",
                    "href": "https://doi.org/10.5067/ATLAS/ATL06.003",
                },
            ],
        },
    ]
    obs = granules.info(grans)

    exp = {
        "Number of available granules": 2,
        "Average size of granules (MB)": 46.49339485165,
        "Total size of all granules (MB)": 92.9867897033,
    }

    assert obs == exp


def test_no_granules_in_search_results():
    ermsg = "Your search returned no results; try different search parameters"
    with pytest.raises(AssertionError, match=ermsg):
        ipx.Query(
            "ATL06", [-55, 68, -48, 71], ["2019-02-20", "2019-02-20"], version="2"
        ).avail_granules()


def test_correct_granule_list_returned():
    reg_a = ipx.Query(
        "ATL06",
        [-55, 68, -48, 71],
        ["2019-02-20", "2019-02-28"],
        version="6",
    )

    (obs_grans,) = reg_a.avail_granules(ids=True)
    exp_grans = [
        "ATL06_20190221121851_08410203_006_02.h5",
        "ATL06_20190222010344_08490205_006_02.h5",
        "ATL06_20190225121032_09020203_006_02.h5",
        "ATL06_20190226005526_09100205_006_02.h5",
    ]
    assert set(obs_grans) == set(exp_grans)


@responses.activate
def test_avail_granule_CMR_error():
    # badreq = re.compile(re.escape('http://cmr.earthdata.nasa.gov/search/granules.json') + r'.*')
    responses.add(
        responses.GET,
        re.compile(re.escape("https://cmr.earthdata.nasa.gov/search/granules") + r".*"),
        status=400,
        json={
            "errors": "temporal start datetime is invalid: [badinput] is not a valid datetime."
        },
    )

    ermsg = "An error was returned from NSIDC in regards to your query: temporal start datetime is invalid: [badinput] is not a valid datetime."
    with pytest.raises(NsidcQueryError, match=re.escape(ermsg)):
        CMRparams = {"temporal": "badinput"}
        # reqparams = {"version": "003", "short_name": "ATL08", "page_size": 1} deprecated
        Granules().get_avail(CMRparams=CMRparams)
