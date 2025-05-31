"""Execution module - bridge to execution_v2.

This module contains:
- executor.py: Main executor (wrapper around V2)
- loop_controller.py: Loop management utilities 
- person_job_executor.py: Simplified PersonJob execution

Legacy components have been removed and replaced by execution_v2.
"""

from .executor import DiagramExecutor

__all__ = [
    "DiagramExecutor"
]