# coding=utf-8

from .dim_ria import DimRiaClient
from .olx import OLXClient
from .olx_api import OLXAPIClient


ALL_CLIENTS = [
    DimRiaClient,
    OLXClient,
    # OLXAPIClient,
]
