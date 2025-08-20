"""Factory functions for creating template services with different configurations."""

import os
from typing import Optional

from .template_service import TemplateService, create_template_service
from .filters import filter_registry


def get_template_service_for_context(context: Optional[str] = None) -> TemplateService:
    if context is None:
        if os.environ.get('DIPEO_CODEGEN_MODE'):
            context = 'codegen'
        elif 'codegen' in os.getcwd():
            context = 'codegen'
        else:
            context = 'default'
    
    if context == 'codegen':
        return create_template_service(['base', 'typescript', 'backend', 'graphql'], profile='codegen')
    elif context == 'api':
        return create_template_service(['base'], profile='full')
    elif context == 'frontend':
        return create_template_service(['base'], profile='full')
    else:
        return create_template_service(['base'], profile='full')


def register_custom_filters(source: str, filters: dict) -> None:
    filter_registry.register_filter_collection(source, filters)


def get_enhanced_template_service() -> TemplateService:
    return create_template_service(['base', 'typescript', 'backend', 'graphql'], profile='codegen')


def get_basic_template_service() -> TemplateService:
    return create_template_service(['base'], profile='full')