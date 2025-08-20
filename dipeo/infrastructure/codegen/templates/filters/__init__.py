"""Template filters package for DiPeO template service.

This package organizes template filters by category, making it easy to:
- Add new filter collections
- Compose filter sets for specific use cases
- Maintain and test filters independently
"""

from .base_filters import BaseFilters
from .typescript_filters import TypeScriptToPythonFilters
from .backend_filters import BackendFilters
from .graphql_filters import TypeScriptToGraphQLFilters
from .registry import FilterRegistry, FilterInfo, create_filter_registry, create_filter_registry_profile, filter_registry

__all__ = [
    'BaseFilters',
    'TypeScriptToPythonFilters',
    'BackendFilters',
    'TypeScriptToGraphQLFilters',
    'FilterRegistry',
    'FilterInfo',
    'create_filter_registry',
    'create_filter_registry_profile',
    'filter_registry',
]