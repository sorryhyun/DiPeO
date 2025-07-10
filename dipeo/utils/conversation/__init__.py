"""Conversation utilities for pure message and memory management."""

from .memory_strategies import (
    MemoryStrategy,
    FullMemoryStrategy,
    WindowMemoryStrategy,
    SummaryMemoryStrategy,
    TokenLimitMemoryStrategy,
    MemoryStrategyFactory
)
from .message_formatter import MessageFormatter
from .forgetting_handler import OnEveryTurnHandler
from .state_utils import (
    ConversationStateManager,
    should_forget_messages,
    apply_forgetting_strategy,
    extract_conversation_messages,
    has_conversation_input,
    consolidate_conversation_messages,
)

__all__ = [
    # Memory strategies
    'MemoryStrategy',
    'FullMemoryStrategy',
    'WindowMemoryStrategy',
    'SummaryMemoryStrategy',
    'TokenLimitMemoryStrategy',
    'MemoryStrategyFactory',
    # Message formatting
    'MessageFormatter',
    # Forgetting handlers
    'OnEveryTurnHandler',
    # State management
    'ConversationStateManager',
    'should_forget_messages',
    'apply_forgetting_strategy',
    'extract_conversation_messages',
    'has_conversation_input',
    'consolidate_conversation_messages',
]