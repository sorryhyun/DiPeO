"""
DiPeO Domain Models

This package contains the shared domain models for the DiPeO project.
These models are auto-generated from TypeScript definitions.
"""

__version__ = "0.1.0"

# Re-export service utilities from config for backward compatibility
from dipeo.config import (
    LLM_SERVICE_TYPES,
    api_service_type_to_llm_service,
    get_llm_service_types,
    get_non_llm_service_types,
    is_llm_service,
    is_valid_api_service_type,
    is_valid_llm_service,
    llm_service_to_api_service_type,
)

__all__ = [
    "LLM_SERVICE_TYPES",
    "api_service_type_to_llm_service",
    "get_llm_service_types",
    "get_non_llm_service_types",
    # Service utilities
    "is_llm_service",
    "is_valid_api_service_type",
    "is_valid_llm_service",
    "llm_service_to_api_service_type",
]
