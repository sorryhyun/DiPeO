"""Application services - DEPRECATED.

This module is deprecated. Import from the new per-context locations:
- dipeo.application.execution.orchestrators for ExecutionOrchestrator
- dipeo.application.integrations.use_cases for APIKeyService
- dipeo.application.execution.use_cases for CliSessionService
"""

import warnings

# Backward compatibility re-exports with deprecation warnings
def __getattr__(name):
    if name == "ExecutionOrchestrator":
        warnings.warn(
            "Import ExecutionOrchestrator from dipeo.application.execution.orchestrators instead",
            DeprecationWarning,
            stacklevel=2
        )
        from dipeo.application.execution.orchestrators import ExecutionOrchestrator
        return ExecutionOrchestrator
    elif name == "APIKeyService":
        warnings.warn(
            "Import APIKeyService from dipeo.application.integrations.use_cases instead",
            DeprecationWarning,
            stacklevel=2
        )
        from dipeo.application.integrations.use_cases import APIKeyService
        return APIKeyService
    elif name == "CliSessionService":
        warnings.warn(
            "Import CliSessionService from dipeo.application.execution.use_cases instead",
            DeprecationWarning,
            stacklevel=2
        )
        from dipeo.application.execution.use_cases import CliSessionService
        return CliSessionService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ExecutionOrchestrator",
    "APIKeyService",
    "CliSessionService",
]