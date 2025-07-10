"""Conversation domain services."""

# Import from utils layer
from dipeo.utils.conversation import (
    MemoryStrategy,
    FullMemoryStrategy,
    WindowMemoryStrategy,
    SummaryMemoryStrategy,
    TokenLimitMemoryStrategy,
    MemoryStrategyFactory,
    MessageFormatter,
    TemplateProcessor
)

# Keep existing services for backward compatibility
try:
    from .on_every_turn_handler import OnEveryTurnHandler
    from .simple_service import ConversationMemoryService
    from .state_manager import ConversationStateManager
    _legacy_exports = [
        'OnEveryTurnHandler',
        'ConversationMemoryService',
        'ConversationStateManager',
    ]
except ImportError:
    _legacy_exports = []

__all__ = [
    # Re-exported from utils layer
    'MemoryStrategy',
    'FullMemoryStrategy',
    'WindowMemoryStrategy',
    'SummaryMemoryStrategy',
    'TokenLimitMemoryStrategy',
    'MemoryStrategyFactory',
    'MessageFormatter',
    'TemplateProcessor',
] + _legacy_exports