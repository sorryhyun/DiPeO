"""Mutable services for runtime execution state."""

from dependency_injector import providers

from ..base import MutableBaseContainer


# Execution context creation removed - use ExecutionRuntime directly


def _create_conversation_manager():
    """Create conversation manager for managing conversation state."""
    from dipeo.application.services.conversation_manager_impl import ConversationManagerImpl
    return ConversationManagerImpl()


def _create_person_manager():
    """Create person manager for managing person state."""
    from dipeo.application.services.person_manager_impl import PersonManagerImpl
    return PersonManagerImpl()


def _create_tool_configuration_service():
    """Create tool configuration service for converting tool strings to configs."""
    from dipeo.application.services.tool_configuration_service import ToolConfigurationService
    return ToolConfigurationService()


def _create_output_builder():
    """Create output builder for constructing node outputs."""
    from dipeo.application.services.output_builder import OutputBuilder
    return OutputBuilder()


# UnifiedExecutionCoordinator removed - functionality merged into TypedStatefulExecution


def _create_execution_engine(
    service_registry,
    observers=None
):
    """Create stateful execution engine."""
    from dipeo.application.execution.engine import TypedExecutionEngine
    
    return TypedExecutionEngine(
        service_registry=service_registry,
        observers=observers or []
    )


# NodeExecutor removed - using ModernNodeExecutor in TypedExecutionEngine


# PersonJobOrchestratorV2 removed - functionality integrated into PersonJobNodeHandler




def _create_execution_iterator(execution_id, state_store):
    """Create execution iterator for traversing execution."""
    from dipeo.application.execution.iterators.simple_iterator import SimpleExecutionIterator
    return SimpleExecutionIterator(
        execution_id=execution_id,
        state_store=state_store
    )


class DynamicServicesContainer(MutableBaseContainer):
    """Mutable services for runtime execution state.
    
    These services align with dipeo/core/dynamic/ and maintain
    state during diagram execution. Most use Factory providers
    to ensure fresh instances per execution.
    """
    
    config = providers.Configuration()
    
    # Dependencies from other containers
    static = providers.DependenciesContainer()
    business = providers.DependenciesContainer()
    persistence = providers.DependenciesContainer()
    integration = providers.DependenciesContainer()
    
    # State management services - Singletons that manage multiple executions
    conversation_manager = providers.Singleton(_create_conversation_manager)
    person_manager = providers.Singleton(_create_person_manager)
    tool_configuration_service = providers.Singleton(_create_tool_configuration_service)
    output_builder = providers.Singleton(_create_output_builder)
    
    # Execution context removed - use ExecutionRuntime directly in ExecuteDiagramUseCase
    
    # Execution coordination removed - functionality merged into TypedStatefulExecution
    
    # Stateful diagram - Factory for fresh instance per diagram
    
    # Execution engine - Factory for fresh engine per execution
    execution_engine = providers.Factory(
        _create_execution_engine,
        service_registry=providers.Dependency(),  # Injected from application layer
        observers=providers.List(),  # Optional observers
    )
    
    # NodeExecutor removed - ModernNodeExecutor is created directly in TypedExecutionEngine
    
    # LLM executor - Can be singleton as it's stateless
    
    # Person job orchestrator removed - integrated into PersonJobNodeHandler
    
    # Execution iterator - Factory for specific execution traversal
    execution_iterator = providers.Factory(
        _create_execution_iterator,
        state_store=persistence.state_store,
    )