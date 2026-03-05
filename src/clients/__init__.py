# coding=utf-8

import typing as _t

from .dim_ria import DimRiaClient
from .olx import OLXClient
from .olx_api import OLXAPIClient


ALL_CLIENTS = [
    DimRiaClient,
    OLXClient,
    # OLXAPIClient,
]

# Define a type for client names, which can be used in CLI arguments and elsewhere.
ClientName = _t.Literal[*(c.name for c in ALL_CLIENTS)]  # type: ignore

if _t.TYPE_CHECKING:
    ClientName = str
