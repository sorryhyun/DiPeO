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
from .filters import FilterRegistry, create_filter_registry

# New architecture exports
from .drivers import (
    CodegenTemplateService,
    FilterRegistry as DriverFilterRegistry,
    MacroLibrary,
    MacroDefinition,
    create_filter_registry as driver_create_filter_registry,
    get_enhanced_template_service,
    get_basic_template_service,
    get_template_service_for_context,
    create_custom_template_service
)
from .adapters import (
    TemplateEngineAdapter,
    Jinja2Adapter
)

__all__ = [
    # Filter exports
    "FilterRegistry",
    "create_filter_registry",
    # Driver/Service exports
    "CodegenTemplateService",
    "MacroLibrary",
    "MacroDefinition",
    "get_enhanced_template_service",
    "get_basic_template_service",
    "get_template_service_for_context",
    "create_custom_template_service",
    # Adapter exports
    "TemplateEngineAdapter",
    "Jinja2Adapter"
]