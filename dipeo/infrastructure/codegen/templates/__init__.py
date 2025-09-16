"""Template infrastructure for code generation.

This module provides a clean architecture for template processing with:
- Adapters: Low-level template engine implementations (Jinja2, etc.)
- Drivers: High-level orchestration services
- Filters: Language-specific template filters

The architecture follows the drivers/adapters pattern:
- Adapters handle low-level template engine operations
- Drivers provide high-level orchestration and business logic
- Filters provide language-specific transformations
"""

from .adapters import Jinja2Adapter, TemplateEngineAdapter
from .drivers import (
    CodegenTemplateService,
    FilterRegistry,
    MacroDefinition,
    MacroLibrary,
    create_filter_registry,
    get_template_service,
)

__all__ = [
    "CodegenTemplateService",
    "FilterRegistry",
    "Jinja2Adapter",
    "MacroDefinition",
    "MacroLibrary",
    "TemplateEngineAdapter",
    "create_filter_registry",
    "get_template_service",
]
