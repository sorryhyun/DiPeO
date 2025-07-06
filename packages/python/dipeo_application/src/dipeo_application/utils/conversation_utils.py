"""Utility methods for conversation handling."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.utils.conversation_utils is deprecated. "
    "Use dipeo.application.utils.conversation_utils instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.utils.conversation_utils import *

__all__ = ["ConversationUtils", "InputDetector", "MessageBuilder"]