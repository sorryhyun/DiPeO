"""Execution module - bridge to execution_v2.

This module contains:
- executor.py: Main executor (wrapper around V2)

Legacy components have been removed and replaced by execution_v2.
"""

from .executor import DiagramExecutor

__all__ = [
    "DiagramExecutor"
]