"""Integration module for template services.

This module provides factory functions for creating template services
with different configurations for various use cases.
"""

import os
from typing import Optional

from .template_service import (
    TemplateService, 
    create_template_service, 
    create_enhanced_template_service
)
from .filters import filter_registry


def get_template_service_for_context(context: Optional[str] = None) -> TemplateService:
    """Get a template service configured for a specific context.
    
    Args:
        context: Context identifier ('codegen', 'api', 'frontend', etc.)
                If None, detects from environment
                
    Returns:
        Configured TemplateService instance
    """
    # Auto-detect context if not provided
    if context is None:
        if os.environ.get('DIPEO_CODEGEN_MODE'):
            context = 'codegen'
        elif 'codegen' in os.getcwd():
            context = 'codegen'
        else:
            context = 'default'
    
    # Return appropriate service based on context
    if context == 'codegen':
        # Code generation needs TypeScript filters
        return create_enhanced_template_service()
    elif context == 'api':
        # API might need GraphQL filters in the future
        return create_template_service(['base'])
    elif context == 'frontend':
        # Frontend might need React/Vue filters in the future
        return create_template_service(['base'])
    else:
        # Default to just base filters
        return create_template_service(['base'])


def register_custom_filters(source: str, filters: dict) -> None:
    """Register custom filters with the global filter registry.
    
    Args:
        source: Source identifier for the filters
        filters: Dictionary of filter name -> function
    """
    filter_registry.register_filter_collection(source, filters)


# Convenience functions for template_job nodes
def get_enhanced_template_service() -> TemplateService:
    """Get a template service with TypeScript conversion support.
    
    This is the primary function used by template_job nodes.
    """
    return create_enhanced_template_service()


def get_basic_template_service() -> TemplateService:
    """Get a basic template service with only base filters."""
    return create_template_service(['base'])