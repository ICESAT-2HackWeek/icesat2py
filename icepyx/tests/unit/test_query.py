import icepyx as ipx

# ------------------------------------
# 		Generic Query tests
# ------------------------------------

# seem to be adequately covered in docstrings;
# may want to focus on testing specific queries


# ------------------------------------
# 		icepyx-specific tests
# ------------------------------------
def test_icepyx_boundingbox_query():
    reg_a = ipx.Query(
        "ATL06",
        [-64, 66, -55, 72],
        ["2019-02-22", "2019-02-28"],
        start_time="03:30:00",
        end_time="21:30:00",
        version="6",
    )
    obs_tuple = (
        reg_a.product,
        reg_a.dates,
        reg_a.start_time,
        reg_a.end_time,
        reg_a.product_version,
        reg_a.spatial_extent,
    )
    exp_tuple = (
        "ATL06",
        ["2019-02-22", "2019-02-28"],
        "03:30:00",
        "21:30:00",
        "006",
        ("bounding_box", [-64.0, 66.0, -55.0, 72.0]),
    )

    assert obs_tuple == exp_tuple


def test_temporal_properties_cycles_tracks():
    reg_a = ipx.Query(
        "ATL06",
        [-55, 68, -48, 71],
        cycles=["03", "04", "05", "06", "07"],
        tracks=["0849", "0902"],
    )
    exp = ["No temporal parameters set"]
    assert [obs == exp for obs in (reg_a.dates, reg_a.start_time, reg_a.end_time)]


# Tests need to add (given can't do them within docstrings/they're behind NSIDC login)
# reqparams post-order
# product_all_info
# show_custom_options
# any other skipped test in Query...
# note that download_granules doesn't show up as skipped in VS testing...
