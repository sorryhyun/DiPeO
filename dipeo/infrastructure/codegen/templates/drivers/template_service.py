"""High-level template service for code generation orchestration."""

import logging
from typing import Any

from ..adapters import TemplateEngineAdapter
from .filter_registry import FilterRegistry
from .macro_library import MacroDefinition, MacroLibrary

logger = logging.getLogger(__name__)


class CodegenTemplateService:
    """High-level template service for code generation.

    This driver orchestrates template rendering using:
    - A template engine adapter (e.g., Jinja2)
    - Filter collections for different languages/contexts
    - Macro libraries for reusable template fragments

    It provides a clean interface for the application layer while
    delegating low-level operations to the adapter.
    """

    def __init__(
        self,
        adapter: TemplateEngineAdapter,
        filter_registry: FilterRegistry,
        macro_library: MacroLibrary | None = None,
    ):
        """Initialize the template service.

        Args:
            adapter: Template engine adapter for rendering
            filter_registry: Registry of filter collections
            macro_library: Optional macro library
        """
        self._adapter = adapter
        self._filter_registry = filter_registry
        self._macro_library = macro_library or MacroLibrary()
        self._filter_profile: str | None = None
        self._active_filters: list[str] = []

    async def render_template(
        self,
        template_path: str,
        context: dict[str, Any],
        filter_collections: list[str] | None = None,
    ) -> str:
        """Render a template with specified filter collections.

        Args:
            template_path: Path to the template file
            context: Context variables for rendering
            filter_collections: Optional list of filter collection names

        Returns:
            Rendered template string
        """
        # Apply filters if specified
        if filter_collections:
            filters = self._filter_registry.compose_filters(*filter_collections)
            for name, func in filters.items():
                self._adapter.register_filter(name, func)

        # Add macros to context
        context["macros"] = self._macro_library.get_all()

        # Render template
        result = await self._adapter.render(template_path, context)
        return result

    async def render_string(
        self,
        template_str: str,
        context: dict[str, Any],
        filter_collections: list[str] | None = None,
    ) -> str:
        """Render a template string with specified filter collections.

        Args:
            template_str: Template string to render
            context: Context variables for rendering
            filter_collections: Optional list of filter collection names

        Returns:
            Rendered template string
        """
        # Apply filters if specified
        if filter_collections:
            filters = self._filter_registry.compose_filters(*filter_collections)
            for name, func in filters.items():
                self._adapter.register_filter(name, func)

        # Add macros to context
        context["macros"] = self._macro_library.get_all()

        # Render template string
        result = await self._adapter.render_string(template_str, context)
        return result

    def set_filter_profile(self, profile_name: str) -> None:
        """Set the active filter profile.

        Args:
            profile_name: Name of the filter profile to use
        """
        self._filter_profile = profile_name
        filters = self._filter_registry.get_profile_filters(profile_name)

        # Register all filters from the profile
        for name, func in filters.items():
            self._adapter.register_filter(name, func)

    def add_filter_collection(self, collection_name: str) -> None:
        """Add a filter collection to the active set.

        Args:
            collection_name: Name of the filter collection to add
        """
        if collection_name not in self._active_filters:
            self._active_filters.append(collection_name)

            # Get and register the filters
            filters = self._filter_registry.get_collection(collection_name)
            if filters:
                for name, func in filters.items():
                    self._adapter.register_filter(name, func)
                logger.debug(f"Added filter collection '{collection_name}'")

    def remove_filter_collection(self, collection_name: str) -> None:
        """Remove a filter collection from the active set.

        Note: This doesn't unregister individual filters as they may
        be provided by other collections.

        Args:
            collection_name: Name of the filter collection to remove
        """
        if collection_name in self._active_filters:
            self._active_filters.remove(collection_name)
            logger.debug(f"Removed filter collection '{collection_name}'")

    def add_template_directory(self, directory: str) -> None:
        """Add a directory to the template search path.

        Args:
            directory: Directory path to add
        """
        self._adapter.add_template_directory(directory)

    def register_macro(self, macro: MacroDefinition) -> None:
        """Register a custom macro.

        Args:
            macro: Macro definition to register
        """
        self._macro_library.register(macro)
        # Also register with adapter for direct use
        self._adapter.register_macro(macro.name, macro.template)

    def clear_cache(self) -> None:
        """Clear all template caches."""
        self._adapter.clear_cache()

    async def render_with_defaults(self, template_path: str, context: dict[str, Any]) -> str:
        """Render a template with default filter collections.

        Uses the currently active filter profile or collections.

        Args:
            template_path: Path to the template file
            context: Context variables for rendering

        Returns:
            Rendered template string
        """
        # Use active filters if any, otherwise use profile
        filter_collections = self._active_filters if self._active_filters else None
        return await self.render_template(template_path, context, filter_collections)

    def get_macro_library(self) -> MacroLibrary:
        """Get the macro library.

        Returns:
            The macro library instance
        """
        return self._macro_library

    def get_filter_registry(self) -> FilterRegistry:
        """Get the filter registry.

        Returns:
            The filter registry instance
        """
        return self._filter_registry
