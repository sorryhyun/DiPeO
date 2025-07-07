"""
DiPeO Application Package.

Application orchestration layer providing use cases and node handlers.
"""

# Context
from .context.application_execution_context import ApplicationExecutionContext
from .compatibility.unified_context import UnifiedExecutionContext

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

# Execution
from .local_execution import LocalExecutionService
from .execution.server_execution_service import ExecuteDiagramUseCase

__all__ = [
    # Context
    "ApplicationExecutionContext",
    "UnifiedExecutionContext",
    # Engine
    "ExecutionEngine",
    "ExecutionController",
    "LocalExecutionView",
    # Execution
    "LocalExecutionService",
    "ExecuteDiagramUseCase",
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