"""
DiPeO CLI - Simplified Interface

Minimal command-line interface for DiPeO diagram operations.
"""

from .cli import DiPeOCLI
from .server_manager import ServerManager

__version__ = "3.0.0"

__all__ = ["DiPeOCLI", "ServerManager"]
