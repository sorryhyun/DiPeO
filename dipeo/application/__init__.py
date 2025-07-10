"""
DiPeO Application Package.

Application orchestration layer providing use cases and node handlers.
"""

# Context
from .execution.context import ApplicationExecutionContext, UnifiedExecutionContext

# Engine components
from .engine import ExecutionEngine, ExecutionController

# Execution framework (moved from core)
from .execution import (
    BaseNodeHandler,
    HandlerRegistry,
    register_handler,
    get_global_registry,
    ExecutionContext,
    ExecutionOptions,
    NodeDefinition,
    NodeHandler,
    BaseExecutor,
    ExecutorInterface,
)

# Handlers
from dipeo.application.execution.handlers import (
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
# Note: MinimalMessageRouter and MinimalStateStore have been removed

# Utilities
from .utils.conversation_utils import InputDetector, MessageBuilder

# Execution
from .execution.use_cases import ExecuteDiagramUseCase

__all__ = [
    # Context
    "ApplicationExecutionContext",
    "UnifiedExecutionContext",
    # Engine
    "ExecutionEngine",
    "ExecutionController",
    # Execution
    "ExecuteDiagramUseCase",
    # Execution framework (moved from core)
    "BaseNodeHandler",
    "HandlerRegistry",
    "register_handler",
    "get_global_registry",
    "ExecutionContext",
    "ExecutionOptions",
    "NodeDefinition",
    "NodeHandler",
    "BaseExecutor",
    "ExecutorInterface",
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
    # Note: MinimalMessageRouter and MinimalStateStore have been removed
    # Utilities
    "InputDetector",
    "MessageBuilder",
]