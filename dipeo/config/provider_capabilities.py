"""Provider capabilities configuration for all LLM providers."""

from enum import Enum
from typing import Any

from dipeo.infrastructure.llm.drivers.types import ProviderCapabilities, StreamingMode


class ProviderType(str, Enum):
    """LLM provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    CLAUDE_CODE = "claude_code"


# Provider capability definitions
PROVIDER_CAPABILITIES: dict[str, dict[str, Any]] = {
    ProviderType.OPENAI: {
        "supports_async": True,
        "supports_streaming": True,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
        "supports_web_search": True,
        "supports_image_generation": True,
        "supports_computer_use": False,
        "supported_models": {
            "gpt-5-nano-2025-08-07",
            "gpt-5-mini-2025-08-07",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o3",
            "o3-mini",
        },
        "streaming_modes": {StreamingMode.NONE, StreamingMode.SSE},
    },
    ProviderType.ANTHROPIC: {
        "supports_async": True,
        "supports_streaming": True,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
        "supports_web_search": False,  # Not native, but can be added via tools
        "supports_image_generation": False,
        "supports_computer_use": False,  # Computer use is only for Claude Code
        "supported_models": {
            "claude-3-5-sonnet-latest",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-latest",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-latest",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
        },
        "streaming_modes": {StreamingMode.NONE, StreamingMode.SSE},
    },
    ProviderType.GOOGLE: {
        "supports_async": True,
        "supports_streaming": True,
        "supports_tools": True,
        "supports_structured_output": True,
        "supports_vision": True,
        "supports_web_search": True,  # Via tools
        "supports_image_generation": True,  # Via Imagen
        "supports_computer_use": False,
        "supported_models": {
            "gemini-1.5-pro",
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-2.0-flash-exp",
            "gemini-pro",
            "gemini-pro-vision",
            "text-bison-001",
            "chat-bison-001",
        },
        "streaming_modes": {StreamingMode.NONE, StreamingMode.SSE},
    },
    ProviderType.OLLAMA: {
        "supports_async": True,
        "supports_streaming": True,
        "supports_tools": False,  # Ollama doesn't support function calling yet
        "supports_structured_output": False,
        "supports_vision": True,  # Some models like llava support vision
        "supports_web_search": False,
        "supports_image_generation": False,
        "supports_computer_use": False,
        "supported_models": {
            # Popular Ollama models
            "llama3.3",
            "llama3.2",
            "llama3.1",
            "llama3",
            "llama2",
            "mistral",
            "mixtral",
            "gemma",
            "gemma2",
            "phi",
            "phi3",
            "qwen",
            "qwen2",
            "vicuna",
            "orca",
            "neural-chat",
            "starling",
            "codellama",
            "deepseek-coder",
            "llava",  # Vision model
            "bakllava",  # Vision model
        },
        "streaming_modes": {StreamingMode.SSE},
    },
    ProviderType.CLAUDE_CODE: {
        "supports_async": True,
        "supports_streaming": True,
        "supports_tools": False,  # Claude Code SDK doesn't support tools in the same way
        "supports_structured_output": False,  # Limited structured output support
        "supports_vision": False,
        "supports_web_search": False,
        "supports_image_generation": False,
        "supports_computer_use": True,  # Claude Code specific capability
        "supported_models": {
            "claude-code",
            "claude-code-sdk",
        },
        "streaming_modes": {StreamingMode.SSE},
    },
}


def get_provider_capabilities(provider: str) -> dict[str, Any]:
    """Get capabilities for a specific provider.

    Args:
        provider: Provider name or type

    Returns:
        Dictionary of provider capabilities

    Raises:
        ValueError: If provider is not found
    """
    # Normalize provider name
    provider_key = provider.lower().replace("-", "_")

    if provider_key not in PROVIDER_CAPABILITIES:
        raise ValueError(f"Unknown provider: {provider}")

    return PROVIDER_CAPABILITIES[provider_key]


def is_capability_supported(provider: str, capability: str) -> bool:
    """Check if a specific capability is supported by a provider.

    Args:
        provider: Provider name or type
        capability: Capability name (e.g., 'supports_tools', 'supports_vision')

    Returns:
        True if capability is supported, False otherwise
    """
    try:
        capabilities = get_provider_capabilities(provider)
        return capabilities.get(capability, False)
    except ValueError:
        return False


def get_supported_models(provider: str) -> set[str]:
    """Get the set of supported models for a provider.

    Args:
        provider: Provider name or type

    Returns:
        Set of supported model names
    """
    try:
        capabilities = get_provider_capabilities(provider)
        return capabilities.get("supported_models", set())
    except ValueError:
        return set()


def get_streaming_modes(provider: str) -> set[StreamingMode]:
    """Get the set of supported streaming modes for a provider.

    Args:
        provider: Provider name or type

    Returns:
        Set of supported streaming modes
    """
    try:
        capabilities = get_provider_capabilities(provider)
        return capabilities.get("streaming_modes", {StreamingMode.NONE})
    except ValueError:
        return {StreamingMode.NONE}


def get_provider_capabilities_object(
    provider: str, max_context_length: int | None = None, max_output_tokens: int | None = None
) -> ProviderCapabilities:
    """Get a ProviderCapabilities object for a specific provider.

    This function creates a ProviderCapabilities object from the provider's
    configuration dictionary, optionally overriding context and output limits.

    Args:
        provider: Provider name or type
        max_context_length: Optional override for max context length
        max_output_tokens: Optional override for max output tokens

    Returns:
        ProviderCapabilities object with all settings

    Raises:
        ValueError: If provider is not found
    """
    capabilities = get_provider_capabilities(provider)

    return ProviderCapabilities(
        supports_async=capabilities["supports_async"],
        supports_streaming=capabilities["supports_streaming"],
        supports_tools=capabilities["supports_tools"],
        supports_structured_output=capabilities["supports_structured_output"],
        supports_vision=capabilities["supports_vision"],
        supports_web_search=capabilities["supports_web_search"],
        supports_image_generation=capabilities["supports_image_generation"],
        supports_computer_use=capabilities["supports_computer_use"],
        max_context_length=max_context_length or 4096,  # Default if not provided
        max_output_tokens=max_output_tokens,
        supported_models=capabilities["supported_models"],
        streaming_modes=capabilities["streaming_modes"],
    )
