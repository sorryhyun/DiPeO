"""Mutable services for runtime execution state."""

from dependency_injector import containers, providers
from ..base import MutableBaseContainer


def _create_execution_context(diagram_compiler, conversation_manager=None):
    """Create execution context for a diagram execution."""
    from dipeo.application.execution.context import UnifiedExecutionContext
    
    return UnifiedExecutionContext(
        compiler=diagram_compiler,
        conversation_manager=conversation_manager
    )


def _create_conversation_manager():
    """Create conversation manager for managing conversation state."""
    from dipeo.application.services.conversation_manager_impl import ConversationManagerImpl
    return ConversationManagerImpl()


def _create_person_manager():
    """Create person manager for managing person state."""
    from dipeo.application.services.person_manager_impl import PersonManagerImpl
    return PersonManagerImpl()


def _create_stateful_diagram(diagram):
    """Create stateful diagram wrapper."""
    from dipeo.application.execution.stateful_diagram import StatefulExecutableDiagram
    return StatefulExecutableDiagram(diagram)


# UnifiedExecutionCoordinator removed - functionality merged into TypedStatefulExecution


def _create_execution_engine(
    context,
    service_registry,
    state_store,
    message_router
):
    """Create stateful execution engine."""
    from dipeo.application.engine import StatefulExecutionEngine
    
    return StatefulExecutionEngine(
        context=context,
        service_registry=service_registry,
        state_store=state_store,
        message_router=message_router
    )


def _create_node_executor(registry, context):
    """Create node executor for running nodes."""
    from dipeo.application.engine import NodeExecutor
    
    return NodeExecutor(
        handler_registry=registry,
        context=context
    )


def _create_person_job_orchestrator(
    prompt_builder,
    conversation_state_manager,
    llm_executor,
    output_builder,
    conversation_processor,
    memory_transformer,
    conversation_manager
):
    """Create person job orchestrator with all dependencies."""
    from dipeo.application.execution.person_job.orchestrator_v2 import PersonJobOrchestratorV2
    
    return PersonJobOrchestratorV2(
        prompt_builder=prompt_builder,
        conversation_state_manager=conversation_state_manager,
        llm_executor=llm_executor,
        output_builder=output_builder,
        conversation_processor=conversation_processor,
        memory_transformer=memory_transformer,
        conversation_manager=conversation_manager,
    )


def _create_llm_executor():
    """Create LLM executor service."""
    from dipeo.application.services.llm_executor import LLMExecutor
    return LLMExecutor()


def _create_execution_iterator(execution_id, state_store):
    """Create execution iterator for traversing execution."""
    from dipeo.application.execution.iterators import ExecutionIterator
    return ExecutionIterator(
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
    
    # Execution context - Factory for fresh context per execution
    execution_context = providers.Factory(
        _create_execution_context,
        diagram_compiler=static.diagram_compiler,
        conversation_manager=conversation_manager,
    )
    
    # Execution coordination removed - functionality merged into TypedStatefulExecution
    
    # Stateful diagram - Factory for fresh instance per diagram
    stateful_diagram = providers.Factory(_create_stateful_diagram)
    
    # Execution engine - Factory for fresh engine per execution
    execution_engine = providers.Factory(
        _create_execution_engine,
        context=execution_context,
        service_registry=providers.Dependency(),  # Injected from application layer
        state_store=persistence.state_store,
        message_router=persistence.message_router,
    )
    
    # Node executor - Factory for fresh executor per execution
    node_executor = providers.Factory(
        _create_node_executor,
        registry=static.node_registry,
        context=execution_context,
    )
    
    # LLM executor - Can be singleton as it's stateless
    llm_executor = providers.Singleton(_create_llm_executor)
    
    # Person job orchestrator - Factory for fresh instance per execution
    person_job_orchestrator = providers.Factory(
        _create_person_job_orchestrator,
        prompt_builder=business.prompt_builder,
        conversation_state_manager=business.conversation_state_manager,
        llm_executor=llm_executor,
        output_builder=business.output_builder,
        conversation_processor=business.conversation_processor,
        memory_transformer=static.memory_transformer,
        conversation_manager=conversation_manager,
    )
    
    # Execution iterator - Factory for specific execution traversal
    execution_iterator = providers.Factory(
        _create_execution_iterator,
        state_store=persistence.state_store,
    )