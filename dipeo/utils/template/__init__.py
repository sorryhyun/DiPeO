"""Template processing utilities."""

from .processor import (
    TemplateProcessor,
    TemplateService,  # Legacy compatibility
    create_template_context,
    extract_variables,
    process_conditional_template,
    process_template,
    validate_template,
)
from .types import TemplateContext, TemplateResult

__all__ = [
    'TemplateContext',
    'TemplateProcessor',
    'TemplateResult',
    'TemplateService',
    'create_template_context',
    'extract_variables',
    'process_conditional_template',
    'process_template',
    'validate_template',
]