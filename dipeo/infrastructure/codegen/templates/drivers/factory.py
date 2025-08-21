"""Factory functions for creating configured template services."""

import os
from typing import Optional, List
from pathlib import Path

from ..adapters import Jinja2Adapter
from .template_service import CodegenTemplateService
from .filter_registry import create_filter_registry
from .macro_library import MacroLibrary


def get_enhanced_template_service(
    template_dirs: Optional[List[str]] = None
) -> CodegenTemplateService:
    """Create a fully-configured template service for code generation.
    
    This includes all filter collections (base, backend, graphql, typescript)
    and the full macro library.
    
    Args:
        template_dirs: Optional list of template directories
        
    Returns:
        Configured CodegenTemplateService instance
    """
    # Default template directories for code generation
    if template_dirs is None:
        template_dirs = [
            'projects/codegen/templates',
            'projects/codegen/templates/models',
            'projects/codegen/templates/backend',
            'projects/codegen/templates/frontend',
        ]
    
    # Filter existing directories
    existing_dirs = [d for d in template_dirs if Path(d).exists()]
    
    # Create adapter
    adapter = Jinja2Adapter(template_dirs=existing_dirs)
    
    # Create filter registry with all collections
    filter_registry = create_filter_registry()
    
    # Create macro library
    macro_library = MacroLibrary()
    
    # Create service
    service = CodegenTemplateService(
        adapter=adapter,
        filter_registry=filter_registry,
        macro_library=macro_library
    )
    
    # Set codegen profile by default
    service.set_filter_profile('codegen')
    
    return service


def get_basic_template_service(
    template_dirs: Optional[List[str]] = None
) -> CodegenTemplateService:
    """Create a minimal template service with just base filters.
    
    Args:
        template_dirs: Optional list of template directories
        
    Returns:
        Configured CodegenTemplateService instance
    """
    # Filter existing directories
    if template_dirs:
        existing_dirs = [d for d in template_dirs if Path(d).exists()]
    else:
        existing_dirs = []
    
    # Create adapter
    adapter = Jinja2Adapter(template_dirs=existing_dirs)
    
    # Create filter registry with just base filters
    filter_registry = create_filter_registry()
    
    # Create minimal macro library
    macro_library = MacroLibrary()
    
    # Create service
    service = CodegenTemplateService(
        adapter=adapter,
        filter_registry=filter_registry,
        macro_library=macro_library
    )
    
    # Set minimal profile
    service.set_filter_profile('minimal')
    
    return service


def get_template_service_for_context(
    context: Optional[str] = None,
    template_dirs: Optional[List[str]] = None
) -> CodegenTemplateService:
    """Create a template service configured for a specific context.
    
    Args:
        context: Context name ('codegen', 'api', 'frontend', 'backend')
        template_dirs: Optional list of template directories
        
    Returns:
        Configured CodegenTemplateService instance
    """
    # Auto-detect context if not provided
    if context is None:
        if os.environ.get('DIPEO_CODEGEN_MODE'):
            context = 'codegen'
        elif 'codegen' in os.getcwd():
            context = 'codegen'
        else:
            context = 'default'
    
    # Create service based on context
    if context == 'codegen':
        service = get_enhanced_template_service(template_dirs)
    elif context == 'api':
        service = get_basic_template_service(template_dirs)
        service.set_filter_profile('api')
    elif context == 'frontend':
        service = get_basic_template_service(template_dirs)
        service.set_filter_profile('frontend')
    elif context == 'backend':
        service = get_basic_template_service(template_dirs)
        service.set_filter_profile('backend')
    else:
        service = get_basic_template_service(template_dirs)
    
    return service


def create_custom_template_service(
    adapter: Optional[Jinja2Adapter] = None,
    filter_collections: Optional[List[str]] = None,
    template_dirs: Optional[List[str]] = None,
    profile: Optional[str] = None
) -> CodegenTemplateService:
    """Create a custom template service with specific configuration.
    
    Args:
        adapter: Optional custom adapter (creates Jinja2Adapter if not provided)
        filter_collections: List of filter collection names to include
        template_dirs: List of template directories
        profile: Optional filter profile to use
        
    Returns:
        Configured CodegenTemplateService instance
    """
    # Create adapter if not provided
    if adapter is None:
        existing_dirs = []
        if template_dirs:
            existing_dirs = [d for d in template_dirs if Path(d).exists()]
        adapter = Jinja2Adapter(template_dirs=existing_dirs)
    
    # Create filter registry
    filter_registry = create_filter_registry()
    
    # Create macro library
    macro_library = MacroLibrary()
    
    # Create service
    service = CodegenTemplateService(
        adapter=adapter,
        filter_registry=filter_registry,
        macro_library=macro_library
    )
    
    # Apply profile or collections
    if profile:
        service.set_filter_profile(profile)
    elif filter_collections:
        for collection in filter_collections:
            service.add_filter_collection(collection)
    
    return service