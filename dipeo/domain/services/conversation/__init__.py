"""Conversation domain services."""

# New pure domain services
from .memory_strategies import (
    MemoryStrategy,
    FullMemoryStrategy,
    WindowMemoryStrategy,
    SummaryMemoryStrategy,
    TokenLimitMemoryStrategy,
    MemoryStrategyFactory
)
from .message_builder import MessageBuilder
from .template_processor import TemplateProcessor

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
    # New pure domain services
    'MemoryStrategy',
    'FullMemoryStrategy',
    'WindowMemoryStrategy',
    'SummaryMemoryStrategy',
    'TokenLimitMemoryStrategy',
    'MemoryStrategyFactory',
    'MessageBuilder',
    'TemplateProcessor',
] + _legacy_exports