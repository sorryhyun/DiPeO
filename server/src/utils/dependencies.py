
"""
Dependency injection functions for FastAPI.

This module re-exports the dependency functions from app_context
for backward compatibility. All service lifecycle management is
handled by the AppContext class.
"""

from .app_context import (
    get_api_key_service,
    get_llm_service,
    get_diagram_service,
    get_file_service,
    get_memory_service,
    get_app_context,
    lifespan
)

__all__ = [
    'get_api_key_service',
    'get_llm_service', 
    'get_diagram_service',
    'get_file_service',
    'get_memory_service',
    'get_app_context',
    'lifespan'
]