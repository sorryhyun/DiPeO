"""
Utility functions for working with service types
These utilities help distinguish between LLM and non-LLM services
"""

from typing import List, Set

from .models import LLMService, APIServiceType


# Set of APIServiceType values that are LLM services
LLM_SERVICE_TYPES: Set[APIServiceType] = {
    APIServiceType.openai,
    APIServiceType.anthropic,
    APIServiceType.google,
    APIServiceType.gemini,
    APIServiceType.grok,
    APIServiceType.bedrock,
    APIServiceType.vertex,
    APIServiceType.deepseek,
}


def is_llm_service(service: APIServiceType) -> bool:
    """Check if an APIServiceType is an LLM service"""
    return service in LLM_SERVICE_TYPES


def api_service_type_to_llm_service(service: APIServiceType) -> LLMService:
    """
    Convert APIServiceType to LLMService
    
    Raises:
        ValueError: If the APIServiceType is not an LLM service
    """
    if not is_llm_service(service):
        raise ValueError(f'APIServiceType "{service.value}" is not an LLM service')
    
    # Handle special cases
    if service == APIServiceType.gemini:
        return LLMService.google
    
    # Direct mapping for others
    return LLMService(service.value)


def llm_service_to_api_service_type(service: LLMService) -> APIServiceType:
    """Convert LLMService to APIServiceType"""
    # Direct mapping works for all LLMService values
    return APIServiceType(service.value)


def get_llm_service_types() -> List[APIServiceType]:
    """Get all LLM service types"""
    return list(LLM_SERVICE_TYPES)


def get_non_llm_service_types() -> List[APIServiceType]:
    """Get all non-LLM service types"""
    return [service for service in APIServiceType if service not in LLM_SERVICE_TYPES]


def is_valid_llm_service(service: str) -> bool:
    """Type guard to check if a string is a valid LLMService"""
    try:
        LLMService(service)
        return True
    except ValueError:
        return False


def is_valid_api_service_type(service: str) -> bool:
    """Type guard to check if a string is a valid APIServiceType"""
    try:
        APIServiceType(service)
        return True
    except ValueError:
        return False