"""Service configuration and utilities for DiPeO."""

from typing import Set
from dipeo.diagram_generated import APIServiceType, LLMService


# Valid LLM service names
VALID_LLM_SERVICES: Set[str] = {
    "openai",
    "anthropic",
    "claude-code",
    "gemini",
    "google",
    "ollama",
}

# Set of APIServiceType values that are LLM services
LLM_SERVICE_TYPES: set[APIServiceType] = {
    APIServiceType.OPENAI,
    APIServiceType.ANTHROPIC,
    APIServiceType.GOOGLE,
    APIServiceType.GEMINI,
    APIServiceType.BEDROCK,
    APIServiceType.VERTEX,
    APIServiceType.DEEPSEEK,
}


def normalize_service_name(service: str) -> str:
    """Normalize service name to canonical form.
    
    Args:
        service: Service name to normalize
        
    Returns:
        Normalized service name
    """
    normalized = service.lower().strip()

    # Service aliases
    aliases = {
        "claude": "anthropic",
        "claude-sdk": "claude-code",
        "claude_code": "claude-code",
        "chatgpt": "openai",
        "gpt": "openai",
        "gpt-4": "openai",
        "gpt-3.5": "openai",
        "google": "gemini",
        "llama": "ollama",
        "mistral": "ollama",
        "gemma": "ollama",
        "phi": "ollama",
    }

    return aliases.get(normalized, normalized)


def is_llm_service(service: APIServiceType) -> bool:
    """Check if an APIServiceType is an LLM service."""
    return service in LLM_SERVICE_TYPES


def api_service_type_to_llm_service(service: APIServiceType) -> LLMService:
    """Convert APIServiceType to LLMService.
    
    Raises:
        ValueError: If the APIServiceType is not an LLM service
    """
    if not is_llm_service(service):
        raise ValueError(f'APIServiceType "{service.value}" is not an LLM service')
    
    # Handle special cases
    if service == APIServiceType.GEMINI:
        return LLMService.GOOGLE
    
    # Direct mapping for others
    return LLMService(service.value)


def llm_service_to_api_service_type(service: LLMService) -> APIServiceType:
    """Convert LLMService to APIServiceType."""
    # Direct mapping works for all LLMService values
    return APIServiceType(service.value)


def get_llm_service_types() -> list[APIServiceType]:
    """Get all LLM service types."""
    return list(LLM_SERVICE_TYPES)


def get_non_llm_service_types() -> list[APIServiceType]:
    """Get all non-LLM service types."""
    return [service for service in APIServiceType if service not in LLM_SERVICE_TYPES]


def is_valid_llm_service(service: str) -> bool:
    """Type guard to check if a string is a valid LLMService."""
    try:
        LLMService(service)
        return True
    except ValueError:
        return False


def is_valid_api_service_type(service: str) -> bool:
    """Type guard to check if a string is a valid APIServiceType."""
    try:
        APIServiceType(service)
        return True
    except ValueError:
        return False