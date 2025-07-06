"""
DiPeO Application Package.

Application orchestration layer providing use cases and node handlers.
"""

# Context
from .context.application_execution_context import ApplicationExecutionContext

# Engine components
from .engine import ExecutionEngine, ExecutionController, LocalExecutionView

# Handlers
from .handlers import (
    StartNodeHandler,
    EndpointNodeHandler,
    ConditionNodeHandler,
    DBNodeHandler,
    HookNodeHandler,
    PersonJobNodeHandler,
    PersonBatchJobNodeHandler,
    ApiJobNodeHandler,
    CodeJobNodeHandler,
    NotionNodeHandler,
    JobNodeHandler,
    UserResponseNodeHandler,
)

# Services
from .services import MinimalMessageRouter, MinimalStateStore

# Utilities
from .utils.conversation_utils import ConversationUtils, InputDetector, MessageBuilder
from .utils.template import substitute_template

__all__ = [
    # Context
    "ApplicationExecutionContext",
    # Engine
    "ExecutionEngine",
    "ExecutionController",
    "LocalExecutionView",
    # Handlers
    "StartNodeHandler",
    "EndpointNodeHandler",
    "ConditionNodeHandler",
    "DBNodeHandler",
    "HookNodeHandler",
    "PersonJobNodeHandler",
    "PersonBatchJobNodeHandler",
    "ApiJobNodeHandler",
    "CodeJobNodeHandler",
    "NotionNodeHandler",
    "JobNodeHandler",
    "UserResponseNodeHandler",
    # Services
    "MinimalMessageRouter",
    "MinimalStateStore",
    # Utilities
    "ConversationUtils",
    "InputDetector",
    "MessageBuilder",
    "substitute_template",
]