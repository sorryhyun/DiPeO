"""Infrastructure services - DEPRECATED.

This module is deprecated. Import from the new per-context driver locations:
- dipeo.infrastructure.llm.drivers for LLM services
- dipeo.infrastructure.diagram.drivers for diagram services
- dipeo.infrastructure.integrations.drivers for API services
- dipeo.infrastructure.shared.template.drivers for template services
"""

import warnings

# Backward compatibility re-exports with deprecation warnings
from dipeo.infrastructure.shared.template.drivers.jinja_template.template_service import (
    TemplateService, 
    create_template_service, 
    create_enhanced_template_service
)
from dipeo.infrastructure.shared.template.drivers.jinja_template.template_integration import (
    get_enhanced_template_service, 
    get_template_service_for_context
)
from dipeo.infrastructure.shared.template.drivers.jinja_template.filters import (
    FilterRegistry, 
    create_filter_registry
)

warnings.warn(
    "Import from dipeo.infrastructure.shared.template.drivers instead of dipeo.infrastructure.services",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    "TemplateService",
    "create_template_service",
    "create_enhanced_template_service",
    "get_enhanced_template_service",
    "get_template_service_for_context",
    "FilterRegistry",
    "create_filter_registry",
]