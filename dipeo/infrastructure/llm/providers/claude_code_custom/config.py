"""Configuration and capabilities for Claude Code Custom provider."""

import os

from claude_agent_sdk import ClaudeAgentOptions

from dipeo.config.base_logger import get_module_logger
from dipeo.config.llm import (
    CLAUDE_MAX_CONTEXT_LENGTH,
    CLAUDE_MAX_OUTPUT_TOKENS,
)
from dipeo.config.provider_capabilities import get_provider_capabilities_object
from dipeo.infrastructure.llm.drivers.types import ProviderCapabilities

logger = get_module_logger(__name__)

FORK_SESSION_SUPPORTED = "fork_session" in getattr(ClaudeAgentOptions, "__dataclass_fields__", {})
FORK_SESSION_ENABLED = (
    FORK_SESSION_SUPPORTED and os.getenv("DIPEO_CLAUDE_FORK_SESSION", "true").lower() == "true"
)

logger.info(
    f"[ClaudeCodeCustom] Fork session supported: {FORK_SESSION_SUPPORTED}, enabled: {FORK_SESSION_ENABLED}"
)


def get_capabilities() -> ProviderCapabilities:
    """Get Claude Code provider capabilities."""
    from dipeo.config.provider_capabilities import ProviderType as ConfigProviderType

    return get_provider_capabilities_object(
        ConfigProviderType.CLAUDE_CODE,
        max_context_length=CLAUDE_MAX_CONTEXT_LENGTH,
        max_output_tokens=CLAUDE_MAX_OUTPUT_TOKENS,
    )
