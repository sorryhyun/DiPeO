"""Jinja2 implementation of TemplateEngineAdapter."""

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jinja2 import (
    ChoiceLoader,
    DictLoader,
    Environment,
    FileSystemLoader,
    StrictUndefined,
    Template,
)

from .base_adapter import TemplateEngineAdapter


class Jinja2Adapter(TemplateEngineAdapter):
    """Jinja2 implementation of the TemplateEngineAdapter protocol.

    This adapter handles all Jinja2-specific operations including:
    - Environment management
    - Template loading and caching
    - Filter and macro registration
    - Template directory management
    """

    def __init__(self, template_dirs: list[str] | None = None):
        """Initialize the Jinja2 adapter.

        Args:
            template_dirs: Optional list of template directories
        """
        self._template_dirs = template_dirs or []
        self._base_templates: dict[str, str] = {}
        self._filters: dict[str, Callable] = {}
        self._macros: dict[str, str] = {}
        self._env: Environment | None = None
        self._template_cache: dict[str, Template] = {}

        # Initialize the environment
        self._setup_environment()

    def _setup_environment(self) -> None:
        """Set up the Jinja2 environment with loaders."""
        # Create file loaders for directories
        file_loaders = []
        for dir_path in self._template_dirs:
            path = Path(dir_path)
            if path.exists():
                file_loaders.append(FileSystemLoader(str(path)))

        # Create dict loader for base templates
        dict_loader = DictLoader(self._base_templates)

        # Combine loaders
        loader = ChoiceLoader([dict_loader, *file_loaders]) if file_loaders else dict_loader

        # Create environment
        self._env = Environment(
            loader=loader,
            trim_blocks=False,
            lstrip_blocks=False,
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )

        # Apply registered filters
        for name, func in self._filters.items():
            self._env.filters[name] = func

    async def render(self, template_path: str, context: dict[str, Any]) -> str:
        """Render a template file with given context.

        Args:
            template_path: Path to the template file
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template string
        """
        if not self._env:
            raise RuntimeError("Jinja2 environment not initialized")

        # Get template (uses cache if available)
        template = self._env.get_template(template_path)

        # Render in executor to avoid blocking
        loop = asyncio.get_event_loop()
        # IMPORTANT: pass context as kwargs, not a single positional dict
        result = await loop.run_in_executor(None, lambda: template.render(**context))
        return result

    async def render_string(self, template_str: str, context: dict[str, Any]) -> str:
        """Render a template string with given context.

        Args:
            template_str: Template string to render
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template string
        """
        if not self._env:
            raise RuntimeError("Jinja2 environment not initialized")

        # Add macros to template string if any
        if self._macros:
            macro_defs = "\n".join(self._macros.values())
            template_str = macro_defs + "\n" + template_str

        # Create template from string
        template = self._env.from_string(template_str)

        # Render in executor to avoid blocking
        loop = asyncio.get_event_loop()
        # Keep per-render isolation; no env.globals updates per request
        result = await loop.run_in_executor(None, lambda: template.render(**context))
        return result

    def register_filter(self, name: str, filter_func: Callable) -> None:
        """Register a custom filter.

        Args:
            name: Name of the filter
            filter_func: Filter function to register
        """
        self._filters[name] = filter_func
        if self._env:
            self._env.filters[name] = filter_func

    def register_macro(self, name: str, macro_def: str) -> None:
        """Register a macro.

        Args:
            name: Name of the macro
            macro_def: Macro definition (Jinja2 macro syntax)
        """
        self._macros[name] = macro_def

    def add_template_directory(self, directory: str) -> None:
        """Add a directory to the template search path.

        Args:
            directory: Directory path to add
        """
        path = Path(directory)
        if not path.exists():
            raise ValueError(f"Template directory does not exist: {directory}")

        self._template_dirs.append(directory)

        # Update the environment's loader
        if self._env:
            current_loader = self._env.loader
            new_file_loader = FileSystemLoader(str(directory))

            if isinstance(current_loader, ChoiceLoader):
                current_loader.loaders.append(new_file_loader)
            else:
                self._env.loader = ChoiceLoader([current_loader, new_file_loader])

    def clear_cache(self) -> None:
        """Clear any template caches."""
        self._template_cache.clear()
        if self._env and hasattr(self._env, "cache"):
            self._env.cache.clear()

    def add_base_template(self, name: str, content: str) -> None:
        """Add a base template to the dictionary loader.

        Args:
            name: Template name
            content: Template content
        """
        self._base_templates[name] = content
        # Reinitialize environment to pick up new base template
        self._setup_environment()

    def register_filter_collection(self, filters: dict[str, Callable]) -> None:
        """Register multiple filters at once.

        Args:
            filters: Dictionary mapping filter names to functions
        """
        for name, func in filters.items():
            self.register_filter(name, func)

    def get_environment(self) -> Environment | None:
        """Get the underlying Jinja2 environment.

        This is useful for advanced use cases that need direct access.

        Returns:
            The Jinja2 Environment instance
        """
        return self._env
