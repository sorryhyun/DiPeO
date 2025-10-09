"""Service configuration and utilities for DiPeO."""

from dipeo.diagram_generated import APIServiceType, LLMService

LLMServiceName = LLMService

VALID_LLM_SERVICES: set[str] = {item for item in LLMService}

LLM_SERVICE_TYPES: set[APIServiceType] = {
    APIServiceType.OPENAI,
    APIServiceType.ANTHROPIC,
    APIServiceType.GOOGLE,
    APIServiceType.GEMINI,
    APIServiceType.OLLAMA,
    APIServiceType.CLAUDE_CODE,
    APIServiceType.CLAUDE_CODE_CUSTOM,
}


def normalize_service_name(service: str) -> str:
    """Normalize service name to canonical form.

    Args:
        service: Service name to normalize

    Returns:
        Normalized service name (LLMServiceName value)
    """
    normalized = service.lower().strip().replace("_", "-")

    aliases = {
        "claude": LLMService.ANTHROPIC,
        "claude-sdk": LLMService.CLAUDE_CODE,
        "claude-code": LLMService.CLAUDE_CODE,
        "claude-code-custom": LLMService.CLAUDE_CODE_CUSTOM,
        "chatgpt": LLMService.OPENAI,
        "gpt": LLMService.OPENAI,
        "gpt-4": LLMService.OPENAI,
        "gpt-3.5": LLMService.OPENAI,
        "google": LLMService.GEMINI,
        "gemini": LLMService.GEMINI,
        "llama": LLMService.OLLAMA,
        "mistral": LLMService.OLLAMA,
        "gemma": LLMService.OLLAMA,
        "phi": LLMService.OLLAMA,
        "openai": LLMService.OPENAI,
        "anthropic": LLMService.ANTHROPIC,
        "ollama": LLMService.OLLAMA,
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
        raise ValueError(f'APIServiceType "{service}" is not an LLM service')

    if service == APIServiceType.GEMINI:
        return LLMService.GOOGLE

    return LLMService(service)


def llm_service_to_api_service_type(service: LLMService) -> APIServiceType:
    """Convert LLMService to APIServiceType."""
    return APIServiceType(service)


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
