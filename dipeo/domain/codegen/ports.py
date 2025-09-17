"""Domain ports for codegen infrastructure services."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Optional, Protocol

from .ir_builder_port import IRData


class IRCachePort(Protocol):
    """Port for IR caching infrastructure."""

    async def get(self, key: str) -> Optional[IRData]:
        """Retrieve cached IR data by key.

        Args:
            key: Cache key for IR data

        Returns:
            Cached IRData if exists, None otherwise
        """
        ...

    async def set(self, key: str, data: IRData, ttl: Optional[int] = None) -> None:
        """Store IR data in cache.

        Args:
            key: Cache key for IR data
            data: IR data to cache
            ttl: Time to live in seconds (optional)
        """
        ...

    async def invalidate(self, key: str) -> bool:
        """Invalidate cached IR data.

        Args:
            key: Cache key to invalidate

        Returns:
            True if key existed and was removed, False otherwise
        """
        ...

    async def clear_all(self) -> None:
        """Clear all cached IR data."""
        ...


class IRBuilderRegistryPort(Protocol):
    """Port for IR builder registry."""

    def register_builder(self, name: str, builder: Any) -> None:
        """Register an IR builder.

        Args:
            name: Unique name for the builder
            builder: IR builder instance
        """
        ...

    def get_builder(self, name: str) -> Optional[Any]:
        """Get a registered IR builder.

        Args:
            name: Builder name

        Returns:
            IR builder instance if registered, None otherwise
        """
        ...

    def list_builders(self) -> list[str]:
        """List all registered builder names.

        Returns:
            List of registered builder names
        """
        ...

    def has_builder(self, name: str) -> bool:
        """Check if a builder is registered.

        Args:
            name: Builder name to check

        Returns:
            True if builder is registered, False otherwise
        """
        ...


class TemplateRendererPort(Protocol):
    """Port for template rendering infrastructure."""

    async def render(
        self, template_name: str, context: dict[str, Any], template_string: Optional[str] = None
    ) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file or identifier
            context: Variables to use in template rendering
            template_string: Optional template string to render directly

        Returns:
            Rendered template string
        """
        ...

    def register_filter(self, name: str, filter_func: Any) -> None:
        """Register a custom template filter.

        Args:
            name: Filter name for use in templates
            filter_func: Function implementing the filter
        """
        ...

    def register_macro(self, name: str, macro_func: Any) -> None:
        """Register a template macro.

        Args:
            name: Macro name for use in templates
            macro_func: Function implementing the macro
        """
        ...

    def list_templates(self) -> list[str]:
        """List available template names.

        Returns:
            List of available template names
        """
        ...
