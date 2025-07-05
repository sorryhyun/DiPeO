"""
DiPeO Domain Models

This package contains the shared domain models for the DiPeO project.
These models are auto-generated from TypeScript definitions.
"""

__version__ = "0.1.0"

# Import all models
from .models import *  # noqa: F401, F403

# Import handle utilities
from .handle_utils import (
    create_handle_id,
    parse_handle_id,
)

# Import service utilities
from .service_utils import (
    is_llm_service,
    api_service_type_to_llm_service,
    llm_service_to_api_service_type,
    get_llm_service_types,
    get_non_llm_service_types,
    is_valid_llm_service,
    is_valid_api_service_type,
    LLM_SERVICE_TYPES,
)

# Rebuild models to resolve forward references
from .models import DomainDiagram

DomainDiagram.model_rebuild()

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
