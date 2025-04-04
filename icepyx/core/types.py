from __future__ import annotations

from typing import Literal, TypedDict, Union

from typing_extensions import NotRequired

ICESat2ProductShortName = Literal[
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
]

CMRParamsBase = TypedDict(
    "CMRParamsBase",
    {
        "temporal": NotRequired[str],
        "options[readable_granule_name][pattern]": NotRequired[str],
        "options[spatial][or]": NotRequired[str],
        "readable_granule_name[]": NotRequired[str],
    },
)


class CMRParamsWithBbox(CMRParamsBase):
    bounding_box: str


class CMRParamsWithPolygon(CMRParamsBase):
    polygon: str


CMRParams = Union[CMRParamsWithBbox, CMRParamsWithPolygon]
