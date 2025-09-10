"""Filter registry for managing template filter collections."""

import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


class FilterRegistry:
    """Registry for managing collections of template filters.

    Filters are functions that transform values in templates.
    The registry allows organizing filters into collections and
    composing them for different use cases.
    """

    def __init__(self):
        """Initialize the filter registry."""
        self._filter_collections: dict[str, dict[str, Callable]] = {}
        self._profiles: dict[str, list[str]] = {}
        self._initialize_default_profiles()

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

    def compose_filters(self, *collection_names: str) -> dict[str, Callable]:
        """Compose multiple filter collections into one.

        Later collections override earlier ones for duplicate filter names.

        Args:
            collection_names: Names of collections to compose

        Returns:
            Combined dictionary of filters
        """
        composed = {}
        for name in collection_names:
            collection = self._filter_collections.get(name)
            if collection:
                composed.update(collection)
            else:
                logger.warning(f"Filter collection '{name}' not found")
        return composed

    def create_profile(self, profile_name: str, collection_names: list[str]) -> None:
        """Create a named profile of filter collections.

        Args:
            profile_name: Name of the profile
            collection_names: List of collection names to include
        """
        self._profiles[profile_name] = collection_names

    def get_profile_filters(self, profile_name: str) -> dict[str, Callable]:
        """Get all filters for a named profile.

        Args:
            profile_name: Name of the profile

        Returns:
            Combined dictionary of filters for the profile
        """
        collection_names = self._profiles.get(profile_name, [])
        return self.compose_filters(*collection_names)

    def list_collections(self) -> list[str]:
        """List all registered filter collections.

        Returns:
            List of collection names
        """
        return list(self._filter_collections.keys())

    def list_profiles(self) -> list[str]:
        """List all defined profiles.

        Returns:
            List of profile names
        """
        return list(self._profiles.keys())

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

    def _initialize_default_profiles(self) -> None:
        """Initialize default filter profiles."""
        self.create_profile("full", ["base", "backend", "graphql", "typescript"])

        self.create_profile("codegen", ["base", "backend", "graphql", "typescript"])

        self.create_profile("minimal", ["base"])

        self.create_profile("backend", ["base", "backend"])

        self.create_profile("frontend", ["base", "typescript"])

        self.create_profile("api", ["base", "graphql"])


def create_filter_registry() -> FilterRegistry:
    """Create a filter registry with standard filter collections loaded.

    Returns:
        Configured FilterRegistry instance
    """
    from ..filters import (
        BackendFilters,
        BaseFilters,
        TypeScriptToGraphQLFilters,
        TypeScriptToPythonFilters,
    )

    registry = FilterRegistry()

    registry.register_collection("base", BaseFilters.get_all_filters())
    registry.register_collection("backend", BackendFilters.get_all_filters())
    registry.register_collection("graphql", TypeScriptToGraphQLFilters.get_all_filters())
    registry.register_collection("typescript", TypeScriptToPythonFilters.get_all_filters())

    return registry
