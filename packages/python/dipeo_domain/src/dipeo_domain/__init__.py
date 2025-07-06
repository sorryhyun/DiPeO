"""
Deprecated: This module has been moved to dipeo.domain

This stub module provides backward compatibility during the migration.
All imports from dipeo_domain will continue to work but will issue deprecation warnings.
Please update your imports to use the new location:

    OLD: from dipeo_domain import DomainPerson
    NEW: from dipeo.domain import DomainPerson
"""

import warnings
import sys
import os

# Issue deprecation warning
warnings.warn(
    "dipeo_domain is deprecated and will be removed in a future version. "
    "Please use 'dipeo.domain' instead. "
    "Update your imports: 'from dipeo_domain import X' -> 'from dipeo.domain import X'",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new location for backward compatibility
try:
    # Add the new location to sys.path temporarily
    dipeo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
    dipeo_module_path = os.path.join(dipeo_root, "dipeo")
    
    # Only add to path if not already there
    if dipeo_module_path not in sys.path:
        sys.path.insert(0, dipeo_module_path)
    
    # Import from new location
    from dipeo.domain import *
    from dipeo.domain import models
    from dipeo.domain import __version__
    
    # Import specific items that were in __all__
    from dipeo.domain import (
        create_handle_id,
        parse_handle_id,
        HandleReference,
        is_llm_service,
        api_service_type_to_llm_service,
        llm_service_to_api_service_type,
        get_llm_service_types,
        get_non_llm_service_types,
        is_valid_llm_service,
        is_valid_api_service_type,
        LLM_SERVICE_TYPES,
    )
    
    # Import models from .models for wildcard compatibility
    from dipeo.domain.models import *
    
    # Import FeatureFlags if it exists
    try:
        from dipeo.domain.service_utils import FeatureFlags
    except ImportError:
        pass
    
    # Create models submodule reference for compatibility
    sys.modules['dipeo_domain.models'] = models
    
    # Preserve the original __all__ list
    __all__ = [
        # Handle utilities
        "create_handle_id",
        "parse_handle_id",
        # Service utilities
        "is_llm_service",
        "api_service_type_to_llm_service",
        "llm_service_to_api_service_type",
        "get_llm_service_types",
        "get_non_llm_service_types",
        "is_valid_llm_service",
        "is_valid_api_service_type",
        "LLM_SERVICE_TYPES",
        # Feature flags
        "FeatureFlags",
    ]
    
except ImportError as e:
    warnings.warn(
        f"Failed to import from new location dipeo.domain: {e}. "
        "Make sure the dipeo package is properly installed.",
        ImportWarning,
        stacklevel=2
    )
    # Re-raise to prevent silent failures
    raise