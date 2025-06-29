"""Core constants shared across DiPeO components."""

# Valid LLM services
VALID_LLM_SERVICES = {
    "openai",
    "anthropic",
    "gemini",
    "grok",
    "google",
    "x",
}

def normalize_service_name(service: str) -> str:
    """Normalize service name to canonical form."""
    normalized = service.lower().strip()
    
    # Service aliases
    aliases = {
        "claude": "anthropic",
        "chatgpt": "openai",
        "gpt": "openai",
        "gpt-4": "openai",
        "gpt-3.5": "openai",
        "google": "gemini",
        "x": "grok",
        "xai": "grok",
        "x-ai": "grok",
    }
    
    return aliases.get(normalized, normalized)