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
    from .aggregation_service import ConversationAggregationService
    from .conversation_analysis_service import ConversationAnalysisService
    from .message_builder_service import MessageBuilderService
    from .message_preparator import MessagePreparator
    from .on_every_turn_handler import OnEveryTurnHandler
    from .simple_service import ConversationMemoryService
    from .state_manager import ConversationStateManager
    _legacy_exports = [
        'ConversationAggregationService',
        'ConversationAnalysisService',
        'MessageBuilderService',
        'MessagePreparator',
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