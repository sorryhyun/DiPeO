"""Claude Code translation module for DiPeO diagrams.

This module provides translation of Claude Code sessions into DiPeO diagrams
through a 3-phase architecture:

1. Preprocess - Session-level processing and preparation
2. Convert - Transform session into diagram structure
3. Post-process - Optimize and clean generated diagrams

Main entry point:
- PhaseCoordinator: Orchestrates the 3-phase translation pipeline
"""

# Main interfaces
# Phase-specific modules (for advanced usage)
from . import convert, post_processing, preprocess
from .phase_coordinator import PhaseCoordinator

__all__ = [
    "PhaseCoordinator",
    "convert",
    "post_processing",
    "preprocess",
]
