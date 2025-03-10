"""
Integration tests
"""

import glob
import json
import os

import pytest

import icepyx as ipx
import icepyx.core.is2ref as is2ref

# Misc notes and needed tests
# test avail data and subsetting success for each input type
# (kml, shp, list of coords, bbox)
# check that downloaded data is subset?
# or is this an NSIDC level test so long as we verify the right info is submitted?


@pytest.fixture(scope="module")
def reg():
    live_reg = ipx.Query(
        "ATL06", [-55, 68, -48, 71], ["2019-02-22", "2019-02-28"], version="006"
    )
    yield live_reg
    del live_reg


@pytest.fixture(scope="module")
def session(reg):
    os.environ = {"EARTHDATA_USERNAME": "icepyx_devteam"}
    ed_obj = reg.session
    yield ed_obj
    ed_obj.close()


########## is2ref module ##########


def test_get_custom_options_output(session):
    obs = is2ref._get_custom_options(session, "ATL06", "006")
    with open("./icepyx/tests/integration/ATL06v06_options.json") as exp_json:
        exp = json.load(exp_json)
        assert all(keys in obs for keys in exp)
        assert all(obs[key] == exp[key] for key in exp)


########## query module ##########
# NOTE: best this test can do at the moment is a successful download with no errors...
@pytest.mark.downloads_data
def test_download_granules_with_subsetting(reg, session):
    path = "./downloads_subset"
    reg.order_granules()
    reg.download_granules(path)


@pytest.mark.downloads_data
def test_download_granules_without_subsetting(reg, session, capsys):
    """
    Test that granules can be ordered from NSIDC and downloaded with the `subset=False`
    option.
    """
    path = "./downloads"

    reg.order_granules(verbose=False, subset=False, email=False)
    out, err = capsys.readouterr()  # capture stdout and stderr
    assert out.startswith(
        "Total number of data order requests is  1  for  3  granules.\n"
        "Data request  1  of  1  is submitting to NSIDC\n"
    )
    assert err == ""

    assert reg.reqparams == {
        "client_string": "icepyx",
        "include_meta": "Y",
        "page_num": 0,
        "page_size": 2000,
        "request_mode": "async",
        "short_name": "ATL06",
        "version": "006",
    }
    assert len(reg.granules.orderIDs) == 2
    assert int(reg.granules.orderIDs[0]) >= 5_000_000_000_000

    reg.download_granules(path=path)
    # check that there are the right number of files of the correct size
    assert len(glob.glob(pathname=f"{path}/ATL06_201902*.iso.xml")) == 3
    h5_paths = sorted(glob.glob(pathname=f"{path}/ATL06_201902*.h5"))
    assert len(h5_paths) == 3
    assert [os.path.getsize(filename=p) for p in h5_paths] == [
        53228429,  # 50.8 MiB
        65120027,  # 62.1 MiB
        49749227,  # 47.4 MiB
    ]
