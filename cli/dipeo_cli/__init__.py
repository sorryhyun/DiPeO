"""
DiPeO CLI Package

A standalone command-line interface for DiPeO diagram operations.
This package is decoupled from the server implementation and communicates
exclusively through the GraphQL API.
"""

__version__ = "2.0.0"
__author__ = "DiPeO Team"

from .commands import run, monitor, convert, stats
from .api_client import DiPeoAPIClient

__all__ = [
    "run",
    "monitor", 
    "convert",
    "stats",
    "DiPeoAPIClient"
]