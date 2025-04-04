import pytest

import icepyx as ipx
from icepyx.quest.quest import Quest


@pytest.fixture
def quest_instance(scope="module", autouse=True):
    bounding_box = [-150, 30, -120, 60]
    date_range = ["2022-06-07", "2022-06-14"]
    my_quest = Quest(spatial_extent=bounding_box, date_range=date_range)
    return my_quest


########## PER-DATASET ADDITION TESTS ##########


# Parameterize these add_dataset tests once more datasets are added
def test_add_is2(quest_instance):
    # Add ATL06 as a test to QUEST

    prod = "ATL06"
    quest_instance.add_icesat2(product=prod)
    exp_key = "icesat2"
    exp_type = ipx.Query

    obs = quest_instance.datasets

    assert type(obs) is dict
    assert exp_key in obs
    assert type(obs[exp_key]) is exp_type
    assert quest_instance.datasets[exp_key].product == prod


def test_add_argo(quest_instance):
    params = ["down_irradiance412", "temperature"]
    quest_instance.add_argo(params=params)
    exp_key = "argo"
    exp_type = ipx.quest.dataset_scripts.argo.Argo

    obs = quest_instance.datasets

    assert type(obs) is dict
    assert exp_key in obs
    assert type(obs[exp_key]) is exp_type
    assert set(quest_instance.datasets[exp_key].params) == set(params)


def test_add_multiple_datasets(quest_instance):
    quest_instance.add_argo(params=["down_irradiance412", "temperature"])
    # print(quest_instance.datasets["argo"].params)

    quest_instance.add_icesat2(product="ATL06")
    # print(quest_instance.datasets["icesat2"].product)

    exp_keys = ["argo", "icesat2"]
    assert set(exp_keys) == set(quest_instance.datasets)


########## ALL DATASET METHODS TESTS ##########


# each of the query functions should be tested in their respective modules
def test_search_all(quest_instance):
    quest_instance.add_argo(params=["down_irradiance412", "temperature"])
    quest_instance.add_icesat2(product="ATL06")

    # Search and test all datasets
    quest_instance.search_all()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"icesat2": {"IDs": True}},
        {"argo": {"presRange": "10,500"}},
        {"icesat2": {"IDs": True}, "argo": {"presRange": "10,500"}},
    ],
)
def test_search_all_kwargs(quest_instance, kwargs):
    quest_instance.search_all(**kwargs)


# TESTS NOT IMPLEMENTED
# def test_download_all():
#     quest_instance.add_argo(params=["down_irradiance412", "temperature"])
#     quest_instance.add_icesat2(product="ATL06")

#   # this will require auth in some cases...
#     quest_instance.download_all()


# @pytest.mark.parametrize(
#     "kwargs",
#     [
#         {"icesat2": {"verbose":True}},
#         {"argo":{"keep_existing":True},
#         {"icesat2":{"verbose":True}, "argo":{"keep_existing":True}
#     ],
# )
# def test_download_all_kwargs(quest_instance, kwargs):
#     pass
