"""Claude Code provider for DiPeO using claude-code-sdk."""

# Apply SDK patches on import to fix compatibility issues
from .sdk_patches import apply_all_patches
from .unified_client import UnifiedClaudeCodeClient

apply_all_patches()

__all__ = ["UnifiedClaudeCodeClient"]
