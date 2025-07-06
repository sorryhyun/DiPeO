"""DiPeO Application Use Cases Package.

This package contains the application layer use cases that orchestrate
domain logic and can be used by both the server and CLI applications.
"""

__version__ = "0.1.0"

# Export handlers
from .handlers import (
    ConditionNodeHandler,
    DBNodeHandler,
    EndpointNodeHandler,
    NotionNodeHandler,
    PersonBatchJobNodeHandler,
    PersonJobNodeHandler,
    StartNodeHandler,
    UserResponseNodeHandler,
)

# Export context protocol
from .context import ApplicationContext

# Export execution service
from .execution import LocalExecutionService

# Export execution engine and observer
from .execution_engine import ExecutionEngine, ExecutionObserver
from .unified_execution_engine import UnifiedExecutionEngine

# Export execution flow controller
from .execution_flow_controller import ExecutionFlowController

# Export engine factory
from .engine_factory import EngineFactory

# Export execution view classes
from .execution_view import LocalExecutionView, NodeView, EdgeView

# Export service registry
from .service_registry import LocalServiceRegistry
from .unified_service_registry import UnifiedServiceRegistry

# Export minimal services
from .services import MinimalStateStore, MinimalMessageRouter

__all__ = [
    # Context
    "ApplicationContext",
    # Execution
    "LocalExecutionService",
    "ExecutionEngine",
    "UnifiedExecutionEngine",
    "ExecutionObserver",
    "ExecutionFlowController",
    "EngineFactory",
    "LocalExecutionView",
    "NodeView",
    "EdgeView",
    # Service Registry
    "LocalServiceRegistry",
    "UnifiedServiceRegistry",
    # Minimal Services
    "MinimalStateStore",
    "MinimalMessageRouter",
    # Handlers
    "ConditionNodeHandler",
    "DBNodeHandler",
    "EndpointNodeHandler",
    "NotionNodeHandler",
    "PersonBatchJobNodeHandler",
    "PersonJobNodeHandler",
    "StartNodeHandler",
    "UserResponseNodeHandler",
]
