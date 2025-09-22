"""
Discovery Utility Modules

Support utilities for discovery scanners including network calculations,
MAC vendor lookups, and protocol detection helpers.
"""

from .network_utils import NetworkUtils
from .vendor_lookup import VendorLookup

__all__ = [
    "NetworkUtils",
    "VendorLookup"
]
