"""Backward compatibility re-export for api module.

This module maintains backward compatibility for imports during the migration
of api to integrations bounded context.

DEPRECATED: Use dipeo.domain.integrations instead.
"""

# Re-export for direct imports
from dipeo.domain.integrations.api_services import APIBusinessLogic
from dipeo.domain.integrations.api_value_objects import RetryPolicy, RetryStrategy

__all__ = [
    "APIBusinessLogic",
    "RetryPolicy",
    "RetryStrategy",
]