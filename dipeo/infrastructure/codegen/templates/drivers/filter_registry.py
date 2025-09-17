"""Filter registry for managing template filter collections."""

import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


class FilterRegistry:
    """Registry for managing collections of template filters.

    Filters are functions that transform values in templates.
    """

    def __init__(self):
        """Initialize the filter registry."""
        self._filter_collections: dict[str, dict[str, Callable]] = {}

    def register_collection(self, name: str, filters: dict[str, Callable]) -> None:
        """Register a collection of filters.

        Args:
            name: Name of the filter collection
            filters: Dictionary mapping filter names to functions
        """
        self._filter_collections[name] = filters

    def get_collection(self, name: str) -> dict[str, Callable] | None:
        """Get a filter collection by name.

        Args:
            name: Name of the filter collection

        Returns:
            Dictionary of filters if found, None otherwise
        """
        return self._filter_collections.get(name)

    def get_all_filters(self) -> dict[str, Callable]:
        """Get all registered filters from all collections.

        Returns:
            Combined dictionary of all filters
        """
        all_filters = {}
        for collection in self._filter_collections.values():
            all_filters.update(collection)
        return all_filters

    def list_collections(self) -> list[str]:
        """List all registered filter collections.

        Returns:
            List of collection names
        """
        return list(self._filter_collections.keys())

    def get_filter_names(self, collection_name: str | None = None) -> set[str]:
        """Get all filter names, optionally from a specific collection.

        Args:
            collection_name: Optional collection to get filters from

        Returns:
            Set of filter names
        """
        if collection_name:
            collection = self._filter_collections.get(collection_name, {})
            return set(collection.keys())
        else:
            all_names = set()
            for collection in self._filter_collections.values():
                all_names.update(collection.keys())
            return all_names


def create_filter_registry() -> FilterRegistry:
    """Create a filter registry with standard filter collections loaded.

    Returns:
        Configured FilterRegistry instance
    """
    from ..filters import (
        CaseFilters,
        FrontendFilters,
        GraphQLFilters,
        PythonFilters,
        StringUtilityFilters,
        TypeConversionFilters,
    )

    registry = FilterRegistry()

    # Register focused filter collections
    registry.register_collection("case", CaseFilters.get_all_filters())
    registry.register_collection("string", StringUtilityFilters.get_all_filters())
    registry.register_collection("type_conversion", TypeConversionFilters.get_all_filters())
    registry.register_collection("python", PythonFilters.get_all_filters())
    registry.register_collection("graphql", GraphQLFilters.get_all_filters())
    registry.register_collection("frontend", FrontendFilters.get_all_filters())

    # Register composite collections for backward compatibility
    base_filters = {}
    base_filters.update(CaseFilters.get_all_filters())
    base_filters.update(StringUtilityFilters.get_all_filters())
    registry.register_collection("base", base_filters)

    backend_filters = {}
    backend_filters.update(PythonFilters.get_all_filters())
    backend_filters.update(TypeConversionFilters.get_all_filters())
    registry.register_collection("backend", backend_filters)

    # TypeScript collection combines type conversion and frontend filters
    typescript_filters = {}
    typescript_filters.update(TypeConversionFilters.get_all_filters())
    typescript_filters.update(FrontendFilters.get_all_filters())
    registry.register_collection("typescript", typescript_filters)

    return registry
