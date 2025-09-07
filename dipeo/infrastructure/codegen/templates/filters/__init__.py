"""Template filters package for DiPeO template service.

This package organizes template filters by category, making it easy to:
- Add new filter collections
- Compose filter sets for specific use cases
- Maintain and test filters independently
"""

from .backend_filters import BackendFilters
from .base_filters import BaseFilters
from .graphql_filters import TypeScriptToGraphQLFilters
from .registry import (
    FilterInfo,
    FilterRegistry,
    create_filter_registry,
    create_filter_registry_profile,
    filter_registry,
)
from .typescript_filters import TypeScriptToPythonFilters

__all__ = [
    "BackendFilters",
    "BaseFilters",
    "FilterInfo",
    "FilterRegistry",
    "TypeScriptToGraphQLFilters",
    "TypeScriptToPythonFilters",
    "create_filter_registry",
    "create_filter_registry_profile",
    "filter_registry",
]
