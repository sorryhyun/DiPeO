"""Consolidated typed execution engine.

This engine directly manages state and execution, removing the need for
a separate ExecutionRuntime wrapper.
"""

import asyncio
import logging
import threading
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Optional

from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.core.execution.execution_tracker import ExecutionTracker, CompletionStatus
from dipeo.core.execution.execution_context import ExecutionContext as CoreExecutionContext
from dipeo.core.execution.runtime_resolver import RuntimeResolver
from dipeo.core.execution.dynamic_order_calculator import DynamicOrderCalculator
from dipeo.core.execution.execution_state_manager import ExecutionStateManager
from dipeo.diagram_generated import (
    ExecutionState,
    NodeExecutionStatus,
    NodeID,
    NodeState,
)
from dipeo.infrastructure.config import get_settings
from dipeo.domain.execution import DomainDynamicOrderCalculator

from dipeo.application.execution.states.node_readiness_checker import NodeReadinessChecker
from dipeo.application.execution.states.state_transition_mixin import StateTransitionMixin
from dipeo.application.execution.states.execution_state_persistence import ExecutionStatePersistence

if TYPE_CHECKING:
    from dipeo.application.registry import ServiceRegistry, ServiceKey
    from dipeo.core.ports import ExecutionObserver
    from dipeo.application.bootstrap import Container

logger = logging.getLogger(__name__)


class TypedExecutionEngine(StateTransitionMixin):
    """Consolidated engine that manages both state and execution.
    
    This engine directly manages:
    - Node state transitions
    - Execution tracking
    - Dynamic order calculation
    - Input resolution
    - Observer notifications
    
    No longer requires a separate ExecutionRuntime wrapper.
    """
    
    def __init__(
        self, 
        service_registry: "ServiceRegistry",
        runtime_resolver: RuntimeResolver,
        order_calculator: Any | None = None,
        state_manager: ExecutionStateManager | None = None,
        observers: list["ExecutionObserver"] | None = None
    ):
        self.service_registry = service_registry
        self.runtime_resolver = runtime_resolver
        self.order_calculator = order_calculator or self._create_default_order_calculator()
        self.state_manager = state_manager  # or self._create_default_state_manager()
        self.observers = observers or []
        self._settings = get_settings()
    
    async def execute(
        self,
        diagram: ExecutableDiagram,
        execution_state: ExecutionState,
        options: dict[str, Any],
        container: Optional["Container"] = None,
        interactive_handler: Any | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute a diagram with integrated state management."""
        
        # Initialize engine state
        engine_state = self._initialize_engine_state(
            diagram, execution_state, container, options
        )
        
        # Notify observers
        execution_id = str(execution_state.id)
        diagram_id = str(execution_state.diagram_id)
        
        for observer in self.observers:
            await observer.on_execution_start(execution_id, diagram_id)
        
        try:
            # Main execution loop
            step_count = 0
            while not self._is_complete(engine_state):
                # Build execution context
                context = self._build_execution_context(engine_state)
                
                # Get ready nodes dynamically
                ready_nodes = self.order_calculator.get_ready_nodes(
                    diagram=diagram,
                    node_states=engine_state['node_states'],
                    context=context
                )
                
                if not ready_nodes:
                    # No nodes ready, wait briefly
                    await asyncio.sleep(self._settings.node_ready_poll_interval)
                    continue
                
                step_count += 1

                # Execute ready nodes in parallel with optional concurrency limit
                # TODO: Make max_concurrent configurable via environment variable or config
                max_concurrent = 20  # Default concurrency limit (increased from 10)
                
                # Create semaphore for concurrency control if needed
                semaphore = asyncio.Semaphore(max_concurrent) if len(ready_nodes) > 1 else None
                
                async def execute_with_semaphore(node):
                    """Execute node with semaphore for concurrency control."""
                    if semaphore:
                        async with semaphore:
                            return await self._execute_node(
                                node=node,
                                diagram=diagram,
                                engine_state=engine_state,
                                execution_id=execution_id,
                                interactive_handler=interactive_handler
                            )
                    else:
                        return await self._execute_node(
                            node=node,
                            diagram=diagram,
                            engine_state=engine_state,
                            execution_id=execution_id,
                            interactive_handler=interactive_handler
                        )
                
                # Execute nodes in parallel if there are multiple, sequentially if just one
                results = {}
                if len(ready_nodes) > 1:
                    # Create tasks for parallel execution
                    tasks = []
                    node_ids = []
                    for node in ready_nodes:
                        task = execute_with_semaphore(node)
                        tasks.append(task)
                        node_ids.append(str(node.id))
                    
                    # Execute all tasks in parallel
                    task_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Map results back to node IDs
                    for node_id, result in zip(node_ids, task_results):
                        if isinstance(result, Exception):
                            # Re-raise exceptions from parallel execution
                            raise result
                        results[node_id] = result
                elif ready_nodes:
                    # Single node, execute directly without overhead
                    node = ready_nodes[0]
                    result = await self._execute_node(
                        node=node,
                        diagram=diagram,
                        engine_state=engine_state,
                        execution_id=execution_id,
                        interactive_handler=interactive_handler
                    )
                    results[str(node.id)] = result
                
                # Calculate progress
                progress = self._calculate_progress(engine_state['node_states'])
                
                # Yield step result
                yield {
                    "type": "step_complete",
                    "step": step_count,
                    "executed_nodes": list(results.keys()),
                    "progress": progress,
                }
            
            # Execution complete
            for observer in self.observers:
                await observer.on_execution_complete(execution_id)
            
            yield {
                "type": "execution_complete",
                "total_steps": step_count,
                "execution_path": [
                    str(node_id) for node_id, state in engine_state['node_states'].items()
                    if state.status == NodeExecutionStatus.COMPLETED
                ],
            }
            
        except Exception as e:
            # Notify observers of error
            for observer in self.observers:
                await observer.on_execution_error(execution_id, str(e))
            
            yield {
                "type": "execution_error",
                "error": str(e),
            }
            raise
    
    def _initialize_engine_state(
        self,
        diagram: ExecutableDiagram,
        execution_state: ExecutionState,
        container: Optional["Container"],
        options: dict[str, Any]
    ) -> dict[str, Any]:
        """Initialize the engine's internal state."""
        # Initialize node states
        node_states: dict[NodeID, NodeState] = {}
        
        # Initialize tracker
        tracker = ExecutionTracker()
        
        # Load persisted state if any
        ExecutionStatePersistence.load_from_state(
            execution_state, 
            node_states, 
            tracker
        )
        
        # Initialize remaining nodes
        for node in diagram.nodes:
            if node.id not in node_states:
                node_states[node.id] = NodeState(
                    status=NodeExecutionStatus.PENDING
                )
        
        # Create readiness checker
        readiness_checker = NodeReadinessChecker(diagram, tracker)
        
        # Extract metadata from options
        metadata = options.get('metadata', {})
        
        return {
            'execution_id': execution_state.id,
            'diagram_id': execution_state.diagram_id,
            'diagram': diagram,
            'node_states': node_states,
            'tracker': tracker,
            'readiness_checker': readiness_checker,
            'variables': execution_state.variables or {},
            'metadata': metadata,
            'current_node_id': [None],
            'container': container,
            'state_lock': threading.Lock()
        }
    
    def _build_execution_context(self, engine_state: dict[str, Any]) -> Any:
        """Build execution context for current state."""
        # Gather node outputs from tracker
        node_outputs = {}
        for node_id in engine_state['node_states']:
            protocol_output = engine_state['tracker'].get_last_output(node_id)
            if protocol_output:
                node_outputs[str(node_id)] = protocol_output
        
        # Get execution counts
        node_exec_counts = {
            str(node_id): engine_state['tracker'].get_execution_count(node_id)
            for node_id in engine_state['node_states']
        }
        
        # Create context using the enhanced ExecutionContext
        context = self._create_enhanced_context(
            engine_state,
            node_outputs,
            node_exec_counts
        )
        
        return context
    
    def _create_enhanced_context(
        self,
        engine_state: dict[str, Any],
        node_outputs: dict[str, Any],
        node_exec_counts: dict[str, int]
    ) -> Any:
        """Create an enhanced execution context with runtime methods."""
        # Create a context wrapper that provides the necessary methods
        class EnhancedContext:
            def __init__(self, state, outputs, counts):
                self._engine_state = state
                self._node_outputs = outputs
                self._node_exec_counts = counts
            
            def get_metadata(self, key: str) -> Any:
                """Get metadata value."""
                return self._engine_state['metadata'].get(key)
            
            def set_metadata(self, key: str, value: Any) -> None:
                """Set metadata value."""
                self._engine_state['metadata'][key] = value
            
            def get_variable(self, name: str) -> Any:
                """Get variable value."""
                return self._engine_state['variables'].get(name)
            
            def set_variable(self, name: str, value: Any) -> None:
                """Set variable value."""
                self._engine_state['variables'][name] = value
            
            @property
            def current_node_id(self) -> Optional[NodeID]:
                """Get current executing node ID."""
                return self._engine_state['current_node_id'][0]
            
            @property
            def execution_id(self) -> str:
                """Get execution ID."""
                return str(self._engine_state['execution_id'])
            
            @property
            def diagram_id(self) -> str:
                """Get diagram ID."""
                return str(self._engine_state['diagram_id'])
            
            # Methods for compatibility with runtime resolver
            def get_node_output(self, node_id: str | NodeID) -> Any:
                """Get output from a node."""
                return self._node_outputs.get(str(node_id))
            
            def get_node_execution_count(self, node_id: str | NodeID) -> int:
                """Get execution count for a node."""
                return self._node_exec_counts.get(str(node_id), 0)
            
            def is_first_execution(self, node_id: str | NodeID) -> bool:
                """Check if this is the first execution of a node."""
                return self.get_node_execution_count(node_id) <= 1
        
        return EnhancedContext(engine_state, node_outputs, node_exec_counts)
    
    async def _execute_node(
        self,
        node: ExecutableNode,
        diagram: ExecutableDiagram,
        engine_state: dict[str, Any],
        execution_id: str,
        interactive_handler: Any | None
    ) -> dict[str, Any]:
        """Execute a single node."""
        # Notify observers
        for observer in self.observers:
            await observer.on_node_start(execution_id, str(node.id))
        
        try:
            # Start execution tracking
            tracker = engine_state['tracker']
            tracker.start_execution(node.id)
            
            # Get handler
            from dipeo.application import get_global_registry
            from dipeo.application.execution.handler_factory import HandlerFactory
            
            registry = get_global_registry()
            if not hasattr(registry, '_service_registry') or registry._service_registry is None:
                HandlerFactory(self.service_registry)
            
            handler = registry.create_handler(node.type)
            
            # Build context for input resolution
            context = self._build_execution_context(engine_state)
            
            # Get incoming edges
            incoming_edges = [
                edge for edge in diagram.edges 
                if edge.target_node_id == node.id
            ]
            
            # Resolve inputs using runtime resolver
            inputs = self.runtime_resolver.resolve_node_inputs(
                node=node,
                incoming_edges=incoming_edges,
                context=context
            )
            
            # Update current node
            engine_state['current_node_id'][0] = node.id
            
            # Prepare services with execution context
            from dipeo.application.registry import ServiceKey
            self.service_registry.register(ServiceKey("diagram"), diagram)
            self.service_registry.register(ServiceKey("execution_context"), {
                "interactive_handler": interactive_handler
            })
            
            # Create a context wrapper for the handler
            handler_context = self._create_handler_context(engine_state)
            
            # Execute handler
            output = await handler.execute(
                node=node,
                context=handler_context,
                inputs=inputs,
                services=self.service_registry
            )
            
            # Handle state transitions based on node type
            await self._handle_node_completion(
                node=node,
                output=output,
                engine_state=engine_state,
                diagram=diagram
            )
            
            # Notify observers
            node_state = engine_state['node_states'][node.id]
            for observer in self.observers:
                await observer.on_node_complete(execution_id, str(node.id), node_state)
            
            # Return result
            if hasattr(output, 'to_dict'):
                return output.to_dict()
            else:
                return {"value": output.value, "metadata": output.metadata}
            
        except Exception as e:
            logger.error(f"Error executing node {node.id}: {e}", exc_info=True)
            for observer in self.observers:
                await observer.on_node_error(execution_id, str(node.id), str(e))
            raise
    
    def _create_handler_context(self, engine_state: dict[str, Any]) -> Any:
        """Create a context object that handlers expect (ExecutionRuntime interface)."""
        # Reference to self for use in nested class
        engine_self = self
        
        # Create a minimal wrapper that provides the ExecutionRuntime interface
        class HandlerContext:
            def __init__(self, state):
                self._state = state
                self._tracker = state['tracker']
                self._node_states = state['node_states']
                self._service_registry = engine_self.service_registry
                self._container = state['container']
                self.metadata = state['metadata']
                self._variables = state['variables']
                self._current_node_id = state['current_node_id']
                self._state_lock = state['state_lock']
                self._readiness_checker = state['readiness_checker']
            
            @property
            def diagram(self):
                return self._state['diagram']
            
            @property
            def execution_id(self):
                return str(self._state['execution_id'])
            
            @property
            def diagram_id(self):
                return str(self._state['diagram_id'])
            
            @property
            def current_node_id(self):
                return self._current_node_id[0]
            
            @property
            def container(self):
                return self._container
            
            def get_node_state(self, node_id: NodeID) -> Optional[NodeState]:
                return self._node_states.get(node_id)
            
            def set_node_state(self, node_id: NodeID, state: NodeState) -> None:
                self._node_states[node_id] = state
            
            def get_node_output(self, node_id: str) -> Any:
                protocol_output = self._tracker.get_last_output(NodeID(node_id))
                # Return the full protocol output object, not just the value
                # The runtime resolver needs the full object to handle different output types
                return protocol_output
            
            def get_node_result(self, node_id: NodeID) -> Optional[dict[str, Any]]:
                protocol_output = self._tracker.get_last_output(node_id)
                if protocol_output:
                    result = {"value": protocol_output.value}
                    if hasattr(protocol_output, 'metadata') and protocol_output.metadata:
                        result["metadata"] = protocol_output.metadata
                    return result
                return None
            
            def get_node_execution_count(self, node_id: NodeID | str) -> int:
                # Handle both NodeID and string inputs for compatibility
                if isinstance(node_id, str):
                    node_id = NodeID(node_id)
                return self._tracker.get_execution_count(node_id)
            
            def get_variables(self) -> dict[str, Any]:
                return self._variables.copy()
            
            def get_service(self, service_key) -> Any:
                from dipeo.application.registry import ServiceKey
                if isinstance(service_key, ServiceKey):
                    return self._service_registry.get(service_key)
                return self._service_registry.get(ServiceKey(service_key))
            
            @property
            def service_registry(self):
                return self._service_registry
            
            def create_sub_container(self, sub_execution_id: str, config_overrides: Optional[dict] = None):
                if self._container is None:
                    return None
                return self._container.create_sub_container(
                    parent_execution_id=self.execution_id,
                    sub_execution_id=sub_execution_id,
                    config_overrides=config_overrides or {}
                )
            
            # State transition methods - use engine's methods
            def transition_node_to_completed(self, node_id: NodeID, output: Any) -> None:
                with self._state_lock:
                    engine_self._transition_node_to_completed(
                        node_id, output, self._node_states, self._tracker
                    )
            
            def transition_node_to_maxiter(self, node_id: NodeID, output: Any) -> None:
                with self._state_lock:
                    engine_self._transition_node_to_maxiter(
                        node_id, output, self._node_states, self._tracker
                    )
            
            def reset_node(self, node_id: NodeID) -> None:
                with self._state_lock:
                    engine_self._reset_node(node_id, self._node_states)
            
            # Additional methods from ExecutionRuntime
            def get_ready_nodes(self) -> list["ExecutableNode"]:
                return [
                    node for node in self.diagram.nodes
                    if self._readiness_checker.is_node_ready(node, self._node_states)
                ]
            
            def is_complete(self) -> bool:
                if any(state.status == NodeExecutionStatus.RUNNING for state in self._node_states.values()):
                    return False
                return len(self.get_ready_nodes()) == 0
            
            def get_completed_nodes(self) -> list[NodeID]:
                return [
                    node_id for node_id, state in self._node_states.items()
                    if state.status == NodeExecutionStatus.COMPLETED
                ]
            
            def get_node(self, node_id: NodeID) -> Optional["ExecutableNode"]:
                return self.diagram.get_node(node_id)
            
            def get_execution_summary(self) -> dict[str, Any]:
                return self._tracker.get_execution_summary()
            
            def has_running_nodes(self) -> bool:
                return any(
                    state.status == NodeExecutionStatus.RUNNING 
                    for state in self._node_states.values()
                )
            
            def count_nodes_by_status(self, statuses: list[str]) -> int:
                status_enums = [NodeExecutionStatus[status] for status in statuses]
                return sum(
                    1 for state in self._node_states.values()
                    if state.status in status_enums
                )
            
            # Add resolve_inputs method for compatibility
            def resolve_inputs(self, node: "ExecutableNode") -> dict[str, Any]:
                # Build context for input resolution
                context = engine_self._build_execution_context(self._state)
                
                # Get incoming edges
                incoming_edges = [
                    edge for edge in self.diagram.edges 
                    if edge.target_node_id == node.id
                ]
                
                # Use runtime resolver
                return engine_self.runtime_resolver.resolve_node_inputs(
                    node=node,
                    incoming_edges=incoming_edges,
                    context=context
                )
            
            # Add to_execution_state for state persistence
            def to_execution_state(self) -> ExecutionState:
                return ExecutionStatePersistence.save_to_state(
                    self._state['execution_id'],
                    self._state['diagram_id'],
                    self.diagram,
                    self._node_states,
                    self._tracker
                )
        
        return HandlerContext(engine_state)
    
    async def _handle_node_completion(
        self,
        node: ExecutableNode,
        output: Any,
        engine_state: dict[str, Any],
        diagram: ExecutableDiagram
    ) -> None:
        """Handle node completion and state transitions."""
        from dipeo.diagram_generated.generated_nodes import PersonJobNode, ConditionNode
        
        node_id = node.id
        tracker = engine_state['tracker']
        node_states = engine_state['node_states']
        
        if isinstance(node, PersonJobNode):
            exec_count = tracker.get_execution_count(node_id)
            
            if exec_count >= node.max_iteration:
                # Max iterations reached
                self._transition_node_to_maxiter(node_id, output, node_states, tracker)
                
                # Reset downstream condition nodes
                outgoing_edges = diagram.get_outgoing_edges(node_id)
                for edge in outgoing_edges:
                    target_node = diagram.get_node(edge.target_node_id)
                    if target_node and isinstance(target_node, ConditionNode):
                        node_state = node_states.get(target_node.id)
                        if node_state and node_state.status == NodeExecutionStatus.COMPLETED:
                            self._reset_node(target_node.id, node_states)
            else:
                # Normal completion, reset for next iteration
                self._transition_node_to_completed(node_id, output, node_states, tracker)
                self._reset_node(node_id, node_states)
        
        elif isinstance(node, ConditionNode):
            # Condition nodes complete normally
            self._transition_node_to_completed(node_id, output, node_states, tracker)
        
        else:
            # All other nodes complete normally
            self._transition_node_to_completed(node_id, output, node_states, tracker)
    
    def _transition_node_to_completed(
        self,
        node_id: NodeID,
        output: Any,
        node_states: dict[NodeID, NodeState],
        tracker: ExecutionTracker
    ) -> None:
        """Transition node to completed state."""
        node_states[node_id] = NodeState(status=NodeExecutionStatus.COMPLETED)
        tracker.complete_execution(
            node_id, 
            CompletionStatus.SUCCESS, 
            output=output
        )
    
    def _transition_node_to_maxiter(
        self,
        node_id: NodeID,
        output: Any,
        node_states: dict[NodeID, NodeState],
        tracker: ExecutionTracker
    ) -> None:
        """Transition node to max iterations state."""
        node_states[node_id] = NodeState(status=NodeExecutionStatus.MAXITER_REACHED)
        tracker.complete_execution(
            node_id,
            CompletionStatus.MAX_ITER,
            output=output
        )
    
    def _reset_node(
        self,
        node_id: NodeID,
        node_states: dict[NodeID, NodeState]
    ) -> None:
        """Reset node to pending state."""
        node_states[node_id] = NodeState(status=NodeExecutionStatus.PENDING)
    
    def _is_complete(self, engine_state: dict[str, Any]) -> bool:
        """Check if execution is complete."""
        node_states = engine_state['node_states']
        readiness_checker = engine_state['readiness_checker']
        diagram = engine_state['diagram']
        
        # Check if any nodes are running
        if any(state.status == NodeExecutionStatus.RUNNING for state in node_states.values()):
            return False
        
        # Check if any nodes are ready
        ready_nodes = [
            node for node in diagram.nodes
            if readiness_checker.is_node_ready(node, node_states)
        ]
        
        return len(ready_nodes) == 0
    
    def _calculate_progress(self, node_states: dict[NodeID, NodeState]) -> dict[str, Any]:
        """Calculate execution progress."""
        total = len(node_states)
        completed = sum(
            1 for state in node_states.values()
            if state.status in [NodeExecutionStatus.COMPLETED, NodeExecutionStatus.MAXITER_REACHED]
        )
        
        return {
            "total_nodes": total,
            "completed_nodes": completed,
            "percentage": (completed / total * 100) if total > 0 else 0
        }
    
    def _create_default_order_calculator(self) -> Any:
        """Create default order calculator using domain implementation."""
        return DomainDynamicOrderCalculator()
    
    def _create_default_state_manager(self) -> ExecutionStateManager:
        """Create default state manager."""
        # For now, use a simple in-memory implementation
        class InMemoryStateManager(ExecutionStateManager):
            async def save_state(self, execution_id: str, state: dict[str, Any]) -> None:
                """Save state (no-op for in-memory)."""
                pass
            
            async def load_state(self, execution_id: str) -> dict[str, Any] | None:
                """Load state (returns None for in-memory)."""
                return None
            
            async def delete_state(self, execution_id: str) -> None:
                """Delete state (no-op for in-memory)."""
                pass
        
        return InMemoryStateManager()


# Alias for backward compatibility
StatefulExecutionEngine = TypedExecutionEngine