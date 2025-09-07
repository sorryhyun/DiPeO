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

# Filter exports
from .adapters import Jinja2Adapter, TemplateEngineAdapter

# New architecture exports
from .drivers import (
    CodegenTemplateService,
    MacroDefinition,
    MacroLibrary,
    create_custom_template_service,
    get_basic_template_service,
    get_enhanced_template_service,
    get_template_service_for_context,
)
from .drivers import FilterRegistry as DriverFilterRegistry
from .drivers import create_filter_registry as driver_create_filter_registry
from .filters import FilterRegistry, create_filter_registry

__all__ = [
    # Driver/Service exports
    "CodegenTemplateService",
    # Filter exports
    "FilterRegistry",
    "Jinja2Adapter",
    "MacroDefinition",
    "MacroLibrary",
    # Adapter exports
    "TemplateEngineAdapter",
    "create_custom_template_service",
    "create_filter_registry",
    "get_basic_template_service",
    "get_enhanced_template_service",
    "get_template_service_for_context",
]
