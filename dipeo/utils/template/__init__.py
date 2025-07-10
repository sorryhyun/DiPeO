"""Template processing utilities."""

from .processor import (
    TemplateProcessor,
    TemplateService,  # Legacy compatibility
    process_template,
    process_conditional_template,
    extract_variables,
    validate_template,
    create_template_context,
)
from .types import TemplateResult, TemplateContext

__all__ = [
    'TemplateProcessor',
    'TemplateService',
    'TemplateResult',
    'TemplateContext',
    'process_template',
    'process_conditional_template',
    'extract_variables',
    'validate_template',
    'create_template_context',
]