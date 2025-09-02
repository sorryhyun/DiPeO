"""Service configuration and utilities for DiPeO."""

from enum import Enum
from typing import Set
from dipeo.diagram_generated import APIServiceType, LLMService


class LLMServiceName(str, Enum):
    """Canonical LLM service names used throughout DiPeO."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CLAUDE_CODE = "claude-code"
    GEMINI = "gemini"
    GOOGLE = "google"
    OLLAMA = "ollama"


# Valid LLM service names (for backward compatibility)
VALID_LLM_SERVICES: Set[str] = {item.value for item in LLMServiceName}

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
        Normalized service name (LLMServiceName value)
    """
    normalized = service.lower().strip().replace("_", "-")

    # Service aliases mapping to LLMServiceName values
    aliases = {
        "claude": LLMServiceName.ANTHROPIC.value,
        "claude-sdk": LLMServiceName.CLAUDE_CODE.value,
        "claude-code": LLMServiceName.CLAUDE_CODE.value,
        "chatgpt": LLMServiceName.OPENAI.value,
        "gpt": LLMServiceName.OPENAI.value,
        "gpt-4": LLMServiceName.OPENAI.value,
        "gpt-3.5": LLMServiceName.OPENAI.value,
        "google": LLMServiceName.GEMINI.value,
        "gemini": LLMServiceName.GEMINI.value,
        "llama": LLMServiceName.OLLAMA.value,
        "mistral": LLMServiceName.OLLAMA.value,
        "gemma": LLMServiceName.OLLAMA.value,
        "phi": LLMServiceName.OLLAMA.value,
        "openai": LLMServiceName.OPENAI.value,
        "anthropic": LLMServiceName.ANTHROPIC.value,
        "ollama": LLMServiceName.OLLAMA.value,
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