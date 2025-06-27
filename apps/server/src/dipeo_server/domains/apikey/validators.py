"""API Key validation rules."""


from dipeo_server.shared.exceptions import ValidationError


def validate_service_name(service: str, valid_services: set[str]) -> str:
    """Validate and normalize service name."""
    normalized = service.lower().strip()

    # Service aliases
    aliases = {
        "chatgpt": "openai",
        "claude": "anthropic",
        "gemini": "google",
        "xai": "grok",
    }

    normalized = aliases.get(normalized, normalized)

    if normalized not in valid_services:
        raise ValidationError(
            f"Invalid service '{service}'. Must be one of: {', '.join(valid_services)}"
        )

    return normalized


def validate_api_key_format(key: str, service: str) -> None:
    """Validate API key format for specific service."""
    if not key or not key.strip():
        raise ValidationError("API key cannot be empty")

    # Service-specific validation
    if service == "openai" and not key.startswith("sk-"):
        raise ValidationError("OpenAI API keys must start with 'sk-'")
    if service == "anthropic" and not key.startswith("sk-ant-"):
        raise ValidationError("Anthropic API keys must start with 'sk-ant-'")
