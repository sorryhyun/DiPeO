"""Application-layer compilation orchestration.

This package contains the application-layer compiler that orchestrates
domain compilation services.
"""

from .standard_compiler import StandardCompiler

__all__ = ["StandardCompiler"]