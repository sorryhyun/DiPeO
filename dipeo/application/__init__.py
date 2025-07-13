# DiPeO Application Package.

# Context
from .execution.context import UnifiedExecutionContext

# Engine components
from .engine import TypedExecutionEngine

# Execution framework (moved from core)
from .execution import (
    TypedNodeHandler,
    HandlerRegistry,
    register_handler,
    get_global_registry,
    ExecutionContext,
    ExecutionOptions,
    NodeDefinition,
    NodeHandler,
)

# Handlers
from dipeo.application.execution.handlers import (
    StartNodeHandler,
    EndpointNodeHandler,
    ConditionNodeHandler,
    DBTypedNodeHandler,
    HookNodeHandler,
    PersonJobNodeHandler,
    PersonBatchJobNodeHandler,
    ApiJobNodeHandler,
    CodeJobNodeHandler,
    NotionNodeHandler,
    UserResponseNodeHandler,
)

# Services
# Note: MinimalMessageRouter and MinimalStateStore have been removed

# Utilities
from .utils.conversation_utils import InputDetector, MessageBuilder

# Execution
from .execution.use_cases import ExecuteDiagramUseCase

# Protocols
from .protocols import SupportsAPIKey, ExecutionObserver

__all__ = [
    # Context
    "UnifiedExecutionContext",
    # Engine
    "TypedExecutionEngine",
    # Execution
    "ExecuteDiagramUseCase",
    # Execution framework (moved from core)
    "TypedNodeHandler",
    "HandlerRegistry",
    "register_handler",
    "get_global_registry",
    "ExecutionContext",
    "ExecutionOptions",
    "NodeDefinition",
    "NodeHandler",
    # Handlers
    "StartNodeHandler",
    "EndpointNodeHandler",
    "ConditionNodeHandler",
    "DBTypedNodeHandler",
    "HookNodeHandler",
    "PersonJobNodeHandler",
    "PersonBatchJobNodeHandler",
    "ApiJobNodeHandler",
    "CodeJobNodeHandler",
    "NotionNodeHandler",
    "UserResponseNodeHandler",
    # Services
    # Note: MinimalMessageRouter and MinimalStateStore have been removed
    # Utilities
    "InputDetector",
    "MessageBuilder",
    # Protocols
    "SupportsAPIKey",
    "ExecutionObserver",
]