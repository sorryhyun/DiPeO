"""High-level template service for code generation orchestration."""

import logging
from typing import Any

from dipeo.config.base_logger import get_module_logger

from ..adapters import TemplateEngineAdapter
from .filter_registry import FilterRegistry
from .macro_library import MacroDefinition, MacroLibrary

logger = get_module_logger(__name__)


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

    async def render_template(
        self,
        template_path: str,
        context: dict[str, Any],
    ) -> str:
        """Render a template.

        Args:
            template_path: Path to the template file
            context: Context variables for rendering

        Returns:
            Rendered template string
        """
        # Add macros to context
        context["macros"] = self._macro_library.get_all()

        result = await self._adapter.render(template_path, context)
        return result

    async def render_string(
        self,
        template_str: str,
        context: dict[str, Any],
    ) -> str:
        """Render a template string.

        Args:
            template_str: Template string to render
            context: Context variables for rendering

        Returns:
            Rendered template string
        """
        # Add macros to context
        context["macros"] = self._macro_library.get_all()

        result = await self._adapter.render_string(template_str, context)
        return result

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
        self._adapter.register_macro(macro.name, macro.template)

    def clear_cache(self) -> None:
        """Clear all template caches."""
        self._adapter.clear_cache()

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
